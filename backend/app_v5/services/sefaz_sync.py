import logging
import asyncio
from datetime import datetime
from app_v5.core.supabase_client import SupabaseService
from app_v5.services.xml_parser import XMLParserService
from app_v5.services.rule_engine import RuleEngineService

logger = logging.getLogger(__name__)


class SefazSyncService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.parser = XMLParserService()
        self.rule_engine = RuleEngineService()

    async def sync_company_documents(self, empresa_id: str, tenant_id: str):
        """
        Simula a busca de documentos na SEFAZ.
        Em produção, usará o certificado A1 e a API nfeDistDFeInteresse.
        """
        logger.info(f"Iniciando sincronização SEFAZ para empresa {empresa_id}")

        mock_xml = self._get_mock_nfe_xml()

        try:
            # 1. Parse do XML (agora com extração granular)
            nfe_data = self.parser.parse_nfe(mock_xml.encode('utf-8'))

            # 2. Validação via Motor de Regras (item a item)
            validation_result = self.rule_engine.validate_nfe(nfe_data)

            # 3. Persistir nota principal
            client = self.supabase.get_service_client()
            nota_id = self.supabase.insert_nfe_result(
                nfe_data,
                validation_result,
                tenant_id=tenant_id,
                empresa_id=empresa_id
            )

            # 4. Persistir itens detalhados na tabela nfe_items
            items_results = validation_result.get("items_results", [])
            for i, item in enumerate(nfe_data.get("itens", [])):
                item_result = items_results[i] if i < len(items_results) else {}
                client.table("nfe_items").insert({
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

            # 5. Criar alertas gerenciáveis em alerts_management
            for alerta in validation_result.get("alertas", []):
                client.table("alerts_management").insert({
                    "tenant_id": tenant_id,
                    "empresa_id": empresa_id,
                    "nfe_id": nota_id,
                    "rule_id": alerta.get("rule_id"),
                    "status": "open",
                }).execute()

            # 6. Atualizar status da empresa
            client.table("empresas").update({
                "servico_sefaz_ativo": True
            }).eq("id", empresa_id).execute()

            logger.info(f"Nota sincronizada via SEFAZ: {nota_id} ({len(nfe_data.get('itens', []))} itens)")
            return {"status": "success", "nota_id": nota_id, "alertas": len(validation_result.get("alertas", []))}

        except Exception as e:
            logger.error(f"Erro no SEFAZ Sync: {e}")
            return {"status": "error", "message": str(e)}

    def _get_mock_nfe_xml(self):
        """Retorna um XML de NF-e mock com dados granulares para teste."""
        import random
        n_nota = random.randint(50000, 99999)
        chave = f"35231012345678000190550010000{n_nota}1234567890"
        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
            <NFe>
                <infNFe Id="NFe{chave}" versao="4.00">
                    <ide>
                        <nNF>{n_nota}</nNF>
                        <serie>1</serie>
                        <dhEmi>{datetime.now().isoformat()}</dhEmi>
                    </ide>
                    <emit>
                        <CNPJ>12345678000190</CNPJ>
                        <xNome>Fornecedor Sincronizado SEFAZ</xNome>
                    </emit>
                    <dest>
                        <CNPJ>12345678901234</CNPJ>
                    </dest>
                    <det nItem="1">
                        <prod>
                            <xProd>Notebook Dell Inspiron</xProd>
                            <NCM>84713012</NCM>
                            <CFOP>5102</CFOP>
                            <vProd>5000.00</vProd>
                        </prod>
                        <imposto>
                            <ICMS><ICMS00><CST>00</CST></ICMS00></ICMS>
                            <vCBS>44.00</vCBS>
                            <vIBS>4.50</vIBS>
                        </imposto>
                    </det>
                    <det nItem="2">
                        <prod>
                            <xProd>Mouse USB Logitech</xProd>
                            <NCM>84716053</NCM>
                            <CFOP>5102</CFOP>
                            <vProd>150.00</vProd>
                        </prod>
                        <imposto>
                            <ICMS><ICMS00><CST>00</CST></ICMS00></ICMS>
                            <vCBS>1.35</vCBS>
                            <vIBS>0.15</vIBS>
                        </imposto>
                    </det>
                    <total>
                        <ICMSTot>
                            <vNF>5150.00</vNF>
                        </ICMSTot>
                    </total>
                </infNFe>
            </NFe>
        </nfeProc>"""

