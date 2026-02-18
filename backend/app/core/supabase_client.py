import os
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

from cryptography.fernet import Fernet
import json

class SupabaseService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            cls._instance._init_client()
            cls._instance._init_crypto()
        return cls._instance

    def _init_crypto(self):
        """Inicializa a chave de criptografia Fernet (AES-128 em modo CBC com HMAC-SHA256)."""
        key = os.environ.get("MASTER_ENCRYPTION_KEY")
        if not key:
            # Fallback seguro para desenvolvimento (NÃO USAR EM PRODUÇÃO)
            self.fernet = None
        else:
            self.fernet = Fernet(key.encode())

    def encrypt_data(self, data: str) -> str:
        """Criptografa uma string usando a chave mestra."""
        if not self.fernet:
            return data
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Descriptografa uma string usando a chave mestra."""
        if not self.fernet:
            return encrypted_data
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return "[ERRO_AO_DESCRIPTOGRAFAR]"

    def log_audit(self, user_id: str, tenant_id: str, action: str, resource: str, resource_id: str = None, details: dict = None, ip: str = None):
        """Registra uma ação sensível na tabela de auditoria."""
        try:
            admin_client = self.get_service_client()
            admin_client.table("audit_logs").insert({
                "user_id": user_id,
                "tenant_id": tenant_id,
                "action": action,
                "resource": resource,
                "resource_id": resource_id,
                "ip_address": ip,
                "details": details or {}
            }).execute()
        except Exception as e:
            # Log de auditoria não deve quebrar a aplicação, mas deve ser avisado
            print(f"CRITICAL: Falha ao gravar log de auditoria: {e}")

    def _init_client(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        service_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
            
        self.client: Client = create_client(url, key)
        if service_key:
            self.service_client: Client = create_client(url, service_key)
        else:
            self.service_client = None

    def get_client(self) -> Client:
        """
        Retorna o cliente padrão (ANON).
        """
        return self.client
        
    def get_service_client(self) -> Client:
        """
        Retorna o cliente ADMIN (service_role) com privilégios elevados.
        """
        if not self.service_client:
             raise ValueError("SUPABASE_SERVICE_ROLE_KEY not configured!")
        return self.service_client

    def get_client_for_user(self, access_token: str) -> Client:
        """
        Cria e retorna um cliente Supabase autenticado com o token do usuário.
        Isso garante que as políticas RLS do banco sejam aplicadas ao usuário.
        """
        if not access_token:
            return self.client
            
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        # Para criar um cliente autenticado no SDK Python, passamos o token nos headers.
        # Isso ativa o context object auth.uid() e auth.jwt() no PostgreSQL.
        options = ClientOptions(
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        return create_client(url, key, options=options)

    def insert_nfe_result(self, nfe_data: dict, validation_result: dict, tenant_id: str, empresa_id: str = None):
        """
        Insere a Nota Fiscal e seus Alertas no Supabase.
        """
        # 1. Preparar dados da Nota
        nota_payload = {
            "tenant_id": tenant_id,
            "empresa_id": empresa_id,
            "chave_acesso": nfe_data.get("chave_acesso"),
            "numero": nfe_data.get("numero"),
            "serie": nfe_data.get("serie"),
            "data_emissao": nfe_data.get("data_emissao"),
            "emitente_cnpj": nfe_data.get("emitente_cnpj"),
            "emitente_nome": nfe_data.get("emitente_nome"),
            "destinatario_cnpj": nfe_data.get("destinatario_cnpj"),
            "destinatario_nome": nfe_data.get("destinatario_nome"),
            "valor_total": nfe_data.get("valor_total"),
            "valor_cbs": nfe_data.get("valor_cbs"),
            "valor_ibs": nfe_data.get("valor_ibs"),
            "cbs_correto": validation_result["validation_details"]["cbs_ok"],
            "ibs_correto": validation_result["validation_details"]["ibs_ok"],
            "status": validation_result["status"],
            "processado_em": "now()"
        }

        # Tentar vincular empresa automaticamente pelo CNPJ se no payload veio None
        if not empresa_id and nfe_data.get("destinatario_cnpj"):
            try:
                empresa_res = client.table("empresas")\
                    .select("id")\
                    .eq("tenant_id", tenant_id)\
                    .eq("cnpj", nfe_data.get("destinatario_cnpj"))\
                    .execute()
                if empresa_res.data:
                    empresa_id = empresa_res.data[0]['id']
                    nota_payload["empresa_id"] = empresa_id
            except:
                pass

        # 2. Inserir Nota (retornando ID)
        # Usamos o service_client para bypassar RLS em operações de backend
        client = self.get_service_client()
        res = client.table("notas_fiscais").insert(nota_payload).execute()
        
        if not res.data:
            logger.error(f"Erro Supabase: {res}")
            raise Exception(f"Falha ao inserir nota fiscal: {res}")
            
        nota_id = res.data[0]['id']

        # 3. Inserir Alertas
        if validation_result["alertas"]:
            alertas_payload = []
            for alerta in validation_result["alertas"]:
                alertas_payload.append({
                    "tenant_id": tenant_id,
                    "empresa_id": empresa_id,
                    "nota_fiscal_id": nota_id,
                    "tipo": alerta["tipo"],
                    "severidade": alerta["severidade"],
                    "mensagem": alerta["mensagem"],
                    "valor_esperado": alerta["valor_esperado"],
                    "valor_encontrado": alerta["valor_encontrado"],
                    "diferenca": alerta["diferenca"]
                })
            
            client.table("alertas_conformidade").insert(alertas_payload).execute()

        return nota_id
