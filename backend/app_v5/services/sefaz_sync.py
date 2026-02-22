"""
SefazSyncService — Orquestra a sincronização de NF-es via SEFAZ real.
Usa certificado A1 armazenado no banco para autenticar e buscar documentos.
"""
import os
import base64
import logging
from datetime import datetime

from app_v5.core.supabase_client import SupabaseService
from app_v5.services.xml_parser import XMLParserService
from app_v5.services.rule_engine import RuleEngineService
from app_v5.services.sefaz_client import SefazClient

logger = logging.getLogger(__name__)


class SefazSyncService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.parser = XMLParserService()
        self.rule_engine = RuleEngineService()

    async def sync_company_documents(self, empresa_id: str, tenant_id: str) -> dict:
        """
        Sincroniza NF-es de uma empresa com a SEFAZ usando certificado A1 real.
        Busca apenas documentos com NSU maior que o último processado (incremental).
        """
        logger.info(f"SEFAZ SYNC: Iniciando para empresa {empresa_id}")
        admin_client = self.supabase.get_service_client()

        # 1. Carregar certificado do banco
        cert_res = (
            admin_client.table("certificados_a1")
            .select("certificado_enc, senha_enc, ultimo_nsu, ambiente")
            .eq("empresa_id", empresa_id)
            .eq("status", "ativo")
            .maybe_single()
            .execute()
        )

        if not cert_res.data:
            logger.warning(f"SEFAZ SYNC: Nenhum certificado ativo para empresa {empresa_id}")
            return {"status": "error", "message": "Certificado A1 não configurado. Faça upload do certificado."}

        cert_row = cert_res.data
        ambiente = cert_row.get("ambiente", "producao")
        ultimo_nsu = cert_row.get("ultimo_nsu", "000000000000000")

        # 2. Descriptografar certificado + senha
        try:
            cert_b64 = self.supabase.decrypt_data(cert_row["certificado_enc"])
            pfx_bytes = base64.b64decode(cert_b64)
            senha = self.supabase.decrypt_data(cert_row["senha_enc"])
        except Exception as e:
            logger.error(f"SEFAZ SYNC: Erro ao decriptografar certificado: {e}")
            return {"status": "error", "message": "Erro ao carregar certificado. Tente re-fazer o upload."}

        # 3. Buscar CNPJ da empresa
        emp_res = (
            admin_client.table("empresas")
            .select("cnpj, razao_social")
            .eq("id", empresa_id)
            .single()
            .execute()
        )
        if not emp_res.data:
            return {"status": "error", "message": "Empresa não encontrada."}

        cnpj = emp_res.data["cnpj"]
        razao = emp_res.data.get("razao_social", "N/A")

        # 4. Chamar SEFAZ real
        try:
            sefaz = SefazClient(ambiente=ambiente)
            documentos = sefaz.call_sefaz(pfx_bytes, senha, cnpj, ultimo_nsu)
        except RuntimeError as e:
            # Atualizar status do certificado como erro
            admin_client.table("certificados_a1").update(
                {"status": "erro"}
            ).eq("empresa_id", empresa_id).execute()
            logger.error(f"SEFAZ SYNC: Erro na chamada SEFAZ: {e}")
            return {"status": "error", "message": str(e)}

        if not documentos:
            logger.info(f"SEFAZ SYNC: Nenhum documento novo para {razao} (NSU={ultimo_nsu})")
            admin_client.table("certificados_a1").update(
                {"ultimo_sync": datetime.utcnow().isoformat()}
            ).eq("empresa_id", empresa_id).execute()
            return {"status": "success", "notas_processadas": 0, "message": "Nenhuma nota nova."}

        # 5. Processar cada documento retornado
        notas_ok = 0
        notas_erro = 0
        novo_nsu = ultimo_nsu

        for doc in documentos:
            try:
                nfe_data = self.parser.parse_nfe(doc["xml_content"])
                validation_result = self.rule_engine.validate_nfe(nfe_data)

                nota_id = self.supabase.insert_nfe_result(
                    nfe_data,
                    validation_result,
                    tenant_id=tenant_id,
                    empresa_id=empresa_id,
                )

                # Persistir itens
                items_results = validation_result.get("items_results", [])
                for i, item in enumerate(nfe_data.get("itens", [])):
                    item_result = items_results[i] if i < len(items_results) else {}
                    admin_client.table("nfe_items").insert({
                        "tenant_id": tenant_id,
                        "nota_fiscal_id": nota_id,
                        "n_item": item.get("n_item"),
                        "ncm": item.get("ncm"),
                        "cfop": item.get("cfop"),
                        "cst": item.get("cst"),
                        "v_prod": item.get("v_prod"),
                        "v_cbs": item.get("v_cbs"),
                        "v_ibs": item.get("v_ibs"),
                        "cbs_correto": item_result.get("cbs_ok", True),
                        "ibs_correto": item_result.get("ibs_ok", True),
                    }).execute()

                # Gerar alertas
                for alerta in validation_result.get("alertas", []):
                    admin_client.table("alerts_management").insert({
                        "tenant_id": tenant_id,
                        "empresa_id": empresa_id,
                        "nfe_id": nota_id,
                        "rule_id": alerta.get("rule_id"),
                        "status": "open",
                    }).execute()

                # Atualiza NSU máximo processado
                if doc["nsu"] > novo_nsu:
                    novo_nsu = doc["nsu"]

                notas_ok += 1
                logger.info(f"SEFAZ SYNC: Nota {nfe_data.get('chave_acesso', 'N/A')[:20]}... processada")

            except Exception as e:
                notas_erro += 1
                logger.error(f"SEFAZ SYNC: Erro ao processar documento NSU {doc.get('nsu')}: {e}")

        # 6. Atualizar último NSU e timestamp de sync
        admin_client.table("certificados_a1").update({
            "ultimo_nsu": novo_nsu,
            "ultimo_sync": datetime.utcnow().isoformat(),
            "status": "ativo",
        }).eq("empresa_id", empresa_id).execute()

        logger.info(f"SEFAZ SYNC OK — {notas_ok} notas processadas, {notas_erro} erros")
        return {
            "status": "success",
            "notas_processadas": notas_ok,
            "notas_com_erro": notas_erro,
            "novo_nsu": novo_nsu,
            "empresa": razao,
        }
