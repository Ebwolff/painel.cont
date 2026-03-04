"""
SefazSyncService — Orquestra a sincronização de NF-es via SEFAZ real.
Usa certificado A1 armazenado no banco para autenticar e buscar documentos.
"""
import os
import base64
import logging
from datetime import datetime, timezone, timedelta

from app_v5.core.supabase_client import SupabaseService
from app_v5.services.xml_parser import XMLParserService
from app_v5.services.rule_engine import RuleEngineService
from app_v5.services.sefaz_client import SefazClient

logger = logging.getLogger(__name__)

COOLDOWN_MINUTES = 65  # SEFAZ exige 1h; usamos 65min de margem


class SefazSyncService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.parser = XMLParserService()
        self.rule_engine = RuleEngineService()

    async def sync_company_documents(self, empresa_id: str, tenant_id: str) -> dict:
        """
        Sincroniza NF-es de uma empresa com a SEFAZ usando certificado A1 real.
        Busca documentos com NSU maior que o último processado (incremental).
        Inclui: cooldown 656, validação de expiração, lock de deduplicação.
        """
        logger.info(f"SEFAZ SYNC: Iniciando para empresa {empresa_id}")
        admin_client = self.supabase.get_service_client()

        # ══════════════════════════════════════════
        # PRÉ-CHECK 1: Cooldown 656 (Consumo Indevido)
        # ══════════════════════════════════════════
        pre_check = (
            admin_client.table("certificados_a1")
            .select("status, ultimo_sync")
            .eq("empresa_id", empresa_id)
            .maybe_single()
            .execute()
        )
        if pre_check and pre_check.data:
            status_atual = pre_check.data.get("status", "")
            ultimo_sync_str = pre_check.data.get("ultimo_sync")

            # Se status contém "656", verificar se o cooldown já expirou
            if "656" in status_atual and ultimo_sync_str:
                try:
                    last_sync = datetime.fromisoformat(ultimo_sync_str.replace("Z", "+00:00"))
                    elapsed = datetime.now(timezone.utc) - last_sync
                    if elapsed < timedelta(minutes=COOLDOWN_MINUTES):
                        remaining = COOLDOWN_MINUTES - int(elapsed.total_seconds() / 60)
                        logger.info(f"SEFAZ SYNC: Cooldown ativo — {remaining}min restantes")
                        return {
                            "status": "cooldown",
                            "message": f"SEFAZ em cooldown por Consumo Indevido (656). Tente novamente em {remaining} minutos.",
                            "retry_after_minutes": remaining,
                        }
                except (ValueError, TypeError):
                    pass  # Se não conseguir parsear a data, prosseguir

            # PRÉ-CHECK 2: Lock de deduplicação
            if status_atual == "sincronizando":
                logger.warning(f"SEFAZ SYNC: Já em andamento para empresa {empresa_id}")
                return {"status": "already_running", "message": "Sincronização já em andamento. Aguarde."}

        # ══════════════════════════════════════════
        # ADQUIRIR LOCK: status → "sincronizando"
        # ══════════════════════════════════════════
        lock_res = (
            admin_client.table("certificados_a1")
            .update({"status": "sincronizando"})
            .eq("empresa_id", empresa_id)
            .in_("status", ["ativo", "erro"])  # Só tranca se está ativo ou com erro anterior
            .execute()
        )
        if not lock_res.data:
            return {"status": "already_running", "message": "Sincronização já em andamento ou certificado inativo."}

        try:
            # ══════════════════════════════════════
            # 1. Carregar certificado do banco
            # ══════════════════════════════════════
            cert_res = (
                admin_client.table("certificados_a1")
                .select("certificado_enc, senha_enc, ultimo_nsu, ambiente, vencimento")
                .eq("empresa_id", empresa_id)
                .maybe_single()
                .execute()
            )

            if not cert_res or not cert_res.data:
                logger.warning(f"SEFAZ SYNC: Nenhum certificado para empresa {empresa_id}")
                return {"status": "error", "message": "Certificado A1 não configurado. Faça upload do certificado."}

            cert_row = cert_res.data
            ambiente = cert_row.get("ambiente", "producao")
            ultimo_nsu = cert_row.get("ultimo_nsu", "000000000000000")

            # ══════════════════════════════════════
            # PRÉ-CHECK 3: Validar expiração do certificado
            # ══════════════════════════════════════
            vencimento_str = cert_row.get("vencimento")
            if vencimento_str:
                try:
                    vencimento = datetime.fromisoformat(vencimento_str.replace("Z", "+00:00"))
                    if vencimento < datetime.now(timezone.utc):
                        admin_client.table("certificados_a1").update(
                            {"status": "vencido"}
                        ).eq("empresa_id", empresa_id).execute()
                        logger.error(f"SEFAZ SYNC: Certificado vencido em {vencimento.isoformat()}")
                        return {
                            "status": "error",
                            "message": f"Certificado venceu em {vencimento.strftime('%d/%m/%Y')}. Faça upload de um novo certificado.",
                        }
                    dias_restantes = (vencimento - datetime.now(timezone.utc)).days
                    if dias_restantes < 30:
                        logger.warning(f"SEFAZ SYNC: ⚠️ Certificado vence em {dias_restantes} dias!")
                except (ValueError, TypeError):
                    pass

            # ══════════════════════════════════════
            # 2. Descriptografar certificado + senha
            # ══════════════════════════════════════
            try:
                cert_b64 = self.supabase.decrypt_data(cert_row["certificado_enc"])
                pfx_bytes = base64.b64decode(cert_b64)
                senha = self.supabase.decrypt_data(cert_row["senha_enc"])
            except Exception as e:
                logger.error(f"SEFAZ SYNC: Erro ao decriptografar certificado: {e}")
                return {"status": "error", "message": "Erro ao carregar certificado. Tente re-fazer o upload."}

            # ══════════════════════════════════════
            # 3. Buscar CNPJ da empresa
            # ══════════════════════════════════════
            emp_res = (
                admin_client.table("empresas")
                .select("cnpj, razao_social, uf")
                .eq("id", empresa_id)
                .single()
                .execute()
            )
            if not emp_res.data:
                return {"status": "error", "message": "Empresa não encontrada."}

            cnpj = emp_res.data["cnpj"]
            razao = emp_res.data.get("razao_social", "N/A")

            # Mapear UF → código IBGE
            UF_IBGE = {
                "AC": "12", "AL": "27", "AP": "16", "AM": "13", "BA": "29",
                "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
                "MT": "51", "MS": "50", "MG": "31", "PA": "15", "PB": "25",
                "PR": "41", "PE": "26", "PI": "22", "RJ": "33", "RN": "24",
                "RS": "43", "RO": "11", "RR": "14", "SC": "42", "SP": "35",
                "SE": "28", "TO": "17",
            }
            uf_sigla = emp_res.data.get("uf", "SP")
            codigo_uf = UF_IBGE.get(uf_sigla, "35")

            # ══════════════════════════════════════
            # 4. Chamar SEFAZ real
            # ══════════════════════════════════════
            try:
                sefaz = SefazClient(ambiente=ambiente)
                documentos = sefaz.call_sefaz(pfx_bytes, senha, cnpj, ultimo_nsu, codigo_uf)
            except RuntimeError as e:
                error_str = str(e)
                # Se for 656, salvar status especial com timestamp para cooldown
                if "656" in error_str:
                    admin_client.table("certificados_a1").update({
                        "status": f"656: {error_str[:150]}",
                        "ultimo_sync": datetime.now(timezone.utc).isoformat(),
                    }).eq("empresa_id", empresa_id).execute()
                    return {
                        "status": "cooldown",
                        "message": f"SEFAZ bloqueou temporariamente. Tente novamente em {COOLDOWN_MINUTES} minutos.",
                        "retry_after_minutes": COOLDOWN_MINUTES,
                    }
                # Outro erro
                admin_client.table("certificados_a1").update(
                    {"status": f"erro: {error_str[:180]}"}
                ).eq("empresa_id", empresa_id).execute()
                logger.error(f"SEFAZ SYNC: Erro na chamada SEFAZ: {e}")
                return {"status": "error", "message": error_str}

            if not documentos:
                logger.info(f"SEFAZ SYNC: Nenhum documento novo para {razao} (NSU={ultimo_nsu})")
                admin_client.table("certificados_a1").update(
                    {"ultimo_sync": datetime.now(timezone.utc).isoformat()}
                ).eq("empresa_id", empresa_id).execute()
                return {"status": "success", "notas_processadas": 0, "message": "Nenhuma nota nova."}

            # ══════════════════════════════════════
            # 5. Processar cada documento retornado
            # ══════════════════════════════════════
            notas_ok = 0
            notas_erro = 0
            novo_nsu = ultimo_nsu

            for doc in documentos:
                try:
                    nfe_data = self.parser.parse_nfe(doc["xml_content"])
                    is_resumo = nfe_data.get("is_resumo", False)

                    if is_resumo:
                        validation_result = {
                            "status": "pendente_manifestacao",
                            "alertas": [],
                            "validation_details": {"cbs_ok": None, "ibs_ok": None},
                            "items_results": [],
                        }
                    else:
                        validation_result = self.rule_engine.validate_nfe(nfe_data)

                    nota_id = self.supabase.insert_nfe_result(
                        nfe_data, validation_result,
                        tenant_id=tenant_id, empresa_id=empresa_id,
                    )

                    if not is_resumo:
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

                        for alerta in validation_result.get("alertas", []):
                            admin_client.table("alerts_management").insert({
                                "tenant_id": tenant_id,
                                "empresa_id": empresa_id,
                                "nfe_id": nota_id,
                                "rule_id": alerta.get("rule_id"),
                                "status": "open",
                            }).execute()

                    if doc["nsu"] > novo_nsu:
                        novo_nsu = doc["nsu"]

                    notas_ok += 1
                    logger.info(f"SEFAZ SYNC: Nota {nfe_data.get('chave_acesso', 'N/A')[:20]}... processada (Resumo={is_resumo})")

                except Exception as e:
                    notas_erro += 1
                    logger.error(f"SEFAZ SYNC: Erro ao processar documento NSU {doc.get('nsu')}: {e}")

            # ══════════════════════════════════════
            # 6. Atualizar último NSU e timestamp
            # ══════════════════════════════════════
            admin_client.table("certificados_a1").update({
                "ultimo_nsu": novo_nsu,
                "ultimo_sync": datetime.now(timezone.utc).isoformat(),
            }).eq("empresa_id", empresa_id).execute()

            logger.info(f"SEFAZ SYNC OK — {notas_ok} notas processadas, {notas_erro} erros")
            return {
                "status": "success",
                "notas_processadas": notas_ok,
                "notas_com_erro": notas_erro,
                "novo_nsu": novo_nsu,
                "empresa": razao,
            }

        except Exception as e:
            error_msg = f"erro_interno: {str(e)}"[:200]
            admin_client.table("certificados_a1").update(
                {"status": error_msg}
            ).eq("empresa_id", empresa_id).execute()
            logger.error(f"SEFAZ SYNC: Erro fatal geral durante sync: {e}")
            return {"status": "error", "message": str(e)}

        finally:
            # ══════════════════════════════════════
            # LIBERAR LOCK: status → "ativo" (sempre)
            # ══════════════════════════════════════
            try:
                admin_client.table("certificados_a1").update(
                    {"status": "ativo"}
                ).eq("empresa_id", empresa_id).eq("status", "sincronizando").execute()
            except Exception:
                pass  # Se falhar, o status já foi atualizado para erro/656/vencido

