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

    async def sync_company_documents(self, empresa_id: str, tenant_id: str, triggered_by: str = "manual") -> dict:
        """
        Sincroniza NF-es de uma empresa com a SEFAZ usando certificado A1 real.
        Busca documentos com NSU maior que o último processado (incremental).
        Grava o histórico na tabela sync_jobs para observabilidade.
        """
        logger.info(f"SEFAZ SYNC: Iniciando para empresa {empresa_id}")
        admin_client = self.supabase.get_service_client()
        start_time = datetime.now(timezone.utc)
        job_id = None

        # ══════════════════════════════════════════
        # 0. Criar Registro de Job (Observabilidade)
        # ══════════════════════════════════════════
        try:
            job_res = admin_client.table("sync_jobs").insert({
                "tenant_id": tenant_id,
                "empresa_id": empresa_id,
                "status": "running",
                "triggered_by": triggered_by,
                "started_at": start_time.isoformat(),
            }).execute()
            if job_res.data:
                job_id = job_res.data[0]["id"]
                logger.info(f"SEFAZ SYNC: Job {job_id} criado.")
        except Exception as e:
            logger.warning(f"SEFAZ SYNC: Falha ao registrar início do job: {e}")

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
                        msg = f"SEFAZ em cooldown por Consumo Indevido (656). Tente novamente em {remaining} minutos."
                        logger.info(f"SEFAZ SYNC: Cooldown ativo — {remaining}min restantes")
                        
                        if job_id:
                            admin_client.table("sync_jobs").update({
                                "status": "cooldown",
                                "finished_at": datetime.now(timezone.utc).isoformat(),
                                "error_message": msg
                            }).eq("id", job_id).execute()

                        return {
                            "status": "cooldown",
                            "message": msg,
                            "retry_after_minutes": remaining,
                        }
                except (ValueError, TypeError):
                    pass  # Se não conseguir parsear a data, prosseguir

            # PRÉ-CHECK 2: Lock de deduplicação
            if status_atual == "sincronizando":
                msg = "Sincronização já em andamento. Aguarde."
                logger.warning(f"SEFAZ SYNC: Já em andamento para empresa {empresa_id}")
                
                if job_id:
                    admin_client.table("sync_jobs").update({
                        "status": "already_running",
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "error_message": msg
                    }).eq("id", job_id).execute()

                return {"status": "already_running", "message": msg}

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
            msg = "Certificado inativo ou já sincronizando."
            if job_id:
                admin_client.table("sync_jobs").update({
                    "status": "blocked",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": msg
                }).eq("id", job_id).execute()
            return {"status": "already_running", "message": msg}

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
            # ETAPA 1: Processar documentos recebidos
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

                    # Marcar resumos no banco para controle de manifestação
                    if is_resumo:
                        try:
                            admin_client.table("notas_fiscais").update({
                                "is_resumo": True,
                                "manifestado": False,
                            }).eq("id", nota_id).execute()
                        except Exception:
                            pass
                    else:
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

            # ══════════════════════════════════════════
            # ETAPA 2: Manifestar notas pendentes
            # ══════════════════════════════════════════
            import asyncio
            MAX_MANIFESTACOES = 20
            DELAY_ENTRE_MANIFESTACOES = 0.5

            manifestadas = 0
            hit_656 = False

            try:
                pendentes = admin_client.table("notas_fiscais") \
                    .select("id, chave_acesso, n_seq_evento") \
                    .eq("empresa_id", empresa_id) \
                    .eq("is_resumo", True) \
                    .eq("manifestado", False) \
                    .limit(MAX_MANIFESTACOES) \
                    .execute()

                for nota in (pendentes.data or []):
                    chave = nota.get("chave_acesso")
                    if not chave or len(chave) != 44:
                        continue

                    try:
                        result = sefaz.manifest_document(
                            pfx_bytes=pfx_bytes,
                            password=senha,
                            cnpj=cnpj,
                            chave_nfe=chave,
                            uf_empresa=uf_sigla,
                            n_seq_evento=nota.get("n_seq_evento", 1),
                        )

                        if result["sucesso"]:
                            # cStat 135 ou 136
                            admin_client.table("notas_fiscais").update({
                                "manifestado": True,
                                "tipo_manifestacao": "210210",
                                "protocolo_evento": result["protocolo"],
                                "data_manifestacao": datetime.now(timezone.utc).isoformat(),
                            }).eq("id", nota["id"]).execute()
                            manifestadas += 1
                            logger.info(f"SEFAZ MANIFEST: ✅ {chave[:20]}... manifestada (prot={result['protocolo']})")

                        elif result["cStat"] == "573":
                            # Duplicidade — já manifestado
                            admin_client.table("notas_fiscais").update({
                                "manifestado": True,
                                "tipo_manifestacao": "210210",
                                "protocolo_evento": result["protocolo"],
                            }).eq("id", nota["id"]).execute()
                            manifestadas += 1
                            logger.info(f"SEFAZ MANIFEST: Duplicidade (573) para {chave[:20]}...")

                        elif result["cStat"] == "656":
                            logger.warning("SEFAZ MANIFEST: 656 Consumo Indevido — parando manifestação")
                            hit_656 = True
                            break

                        elif result["cStat"] == "580":
                            logger.warning(f"SEFAZ MANIFEST: Evento fora de prazo para {chave[:20]}...")

                        elif result["cStat"] == "217":
                            logger.warning(f"SEFAZ MANIFEST: NF-e não consta na base para {chave[:20]}...")

                        else:
                            logger.warning(f"SEFAZ MANIFEST: cStat={result['cStat']} para {chave[:20]}...")

                    except Exception as e:
                        logger.error(f"SEFAZ MANIFEST: Erro ao manifestar {chave[:20]}...: {e}")

                    # Rate limiting entre manifestações
                    await asyncio.sleep(DELAY_ENTRE_MANIFESTACOES)

            except Exception as e:
                logger.error(f"SEFAZ MANIFEST: Erro geral na etapa de manifestação: {e}")

            # ══════════════════════════════════════════
            # ETAPA 3: Redistribuição pós-manifestação
            # ══════════════════════════════════════════
            notas_completas = 0

            if manifestadas > 0 and not hit_656:
                logger.info(f"SEFAZ SYNC: {manifestadas} notas manifestadas. Buscando XMLs completos...")

                try:
                    docs_completos = sefaz.call_sefaz(pfx_bytes, senha, cnpj, novo_nsu, codigo_uf)

                    for doc in docs_completos:
                        try:
                            nfe_data = self.parser.parse_nfe(doc["xml_content"])
                            is_resumo = nfe_data.get("is_resumo", False)

                            if not is_resumo:
                                validation_result = self.rule_engine.validate_nfe(nfe_data)
                                chave = nfe_data.get("chave_acesso")

                                # Tentar atualizar nota existente (resumo → completa)
                                existing = admin_client.table("notas_fiscais") \
                                    .select("id") \
                                    .eq("chave_acesso", chave) \
                                    .eq("empresa_id", empresa_id) \
                                    .maybe_single().execute()

                                if existing and existing.data:
                                    nota_id = existing.data["id"]
                                    admin_client.table("notas_fiscais").update({
                                        "is_resumo": False,
                                        "emitente_cnpj": nfe_data.get("emitente_cnpj"),
                                        "emitente_nome": nfe_data.get("emitente_nome"),
                                        "valor_total": nfe_data.get("valor_total"),
                                        "numero": nfe_data.get("numero"),
                                        "serie": nfe_data.get("serie"),
                                        "data_emissao": nfe_data.get("data_emissao"),
                                        "status": validation_result.get("status", "processado"),
                                    }).eq("id", nota_id).execute()

                                    # Inserir itens
                                    for item in nfe_data.get("itens", []):
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
                                        }).execute()

                                    notas_completas += 1
                                    logger.info(f"SEFAZ REDISTRIB: ✅ procNFe {chave[:20]}... completo")
                                else:
                                    # Nota nova (não era resumo anterior)
                                    self.supabase.insert_nfe_result(
                                        nfe_data, validation_result,
                                        tenant_id=tenant_id, empresa_id=empresa_id,
                                    )
                                    notas_completas += 1

                            if doc["nsu"] > novo_nsu:
                                novo_nsu = doc["nsu"]

                        except Exception as e:
                            logger.error(f"SEFAZ REDISTRIB: Erro ao processar doc completo: {e}")

                except RuntimeError as e:
                    logger.warning(f"SEFAZ REDISTRIB: Erro na chamada de redistribuição: {e}")
                except Exception as e:
                    logger.error(f"SEFAZ REDISTRIB: Erro geral: {e}")

            # ══════════════════════════════════════
            # ETAPA 4: Atualizar último NSU e timestamp
            # ══════════════════════════════════════
            admin_client.table("certificados_a1").update({
                "ultimo_nsu": novo_nsu,
                "ultimo_sync": datetime.now(timezone.utc).isoformat(),
            }).eq("empresa_id", empresa_id).execute()

            logger.info(f"SEFAZ SYNC OK — {notas_ok} notas, {manifestadas} manifestadas, {notas_completas} completas, {notas_erro} erros")
            return {
                "status": "success",
                "notas_processadas": notas_ok,
                "notas_manifestadas": manifestadas,
                "notas_completas": notas_completas,
                "notas_com_erro": notas_erro,
                "novo_nsu": novo_nsu,
                "empresa": razao,
            }

        except Exception as e:
            error_msg = f"erro_interno: {str(e)}"[:500]
            admin_client.table("certificados_a1").update(
                {"status": f"erro: {error_msg[:170]}"}
            ).eq("empresa_id", empresa_id).execute()
            
            if job_id:
                try:
                    admin_client.table("sync_jobs").update({
                        "status": "error",
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
                        "error_message": error_msg,
                    }).eq("id", job_id).execute()
                except Exception: pass

            logger.error(f"SEFAZ SYNC: Erro fatal geral durante sync: {e}")
            return {"status": "error", "message": str(e)}

        finally:
            # ══════════════════════════════════════
            # 5. Finalizar Job e Liberar Lock
            # ══════════════════════════════════════
            if job_id and 'result' in locals() and result.get("status") == "success":
                try:
                    end_time = datetime.now(timezone.utc)
                    duration_ms = int((end_time - start_time).total_seconds() * 1000)
                    admin_client.table("sync_jobs").update({
                        "status": "success",
                        "finished_at": end_time.isoformat(),
                        "duration_ms": duration_ms,
                        "notas_processadas": result.get("notas_processadas", 0),
                        "notas_manifestadas": result.get("notas_manifestadas", 0),
                        "notas_completas": result.get("notas_completas", 0),
                        "notas_com_erro": result.get("notas_com_erro", 0),
                        "novo_nsu": result.get("novo_nsu"),
                    }).eq("id", job_id).execute()
                except Exception as e:
                    logger.warning(f"SEFAZ SYNC: Falha ao fechar job {job_id}: {e}")

            try:
                admin_client.table("certificados_a1").update(
                    {"status": "ativo"}
                ).eq("empresa_id", empresa_id).eq("status", "sincronizando").execute()
            except Exception:
                pass

