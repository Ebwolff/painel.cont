from lxml import etree
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class XMLParserService:
    """
    Serviço especializado em extrair dados de NF-e (Nota Fiscal Eletrônica)
    focado nos campos da Reforma Tributária.
    """
    
    NAMESPACES = {
        'nfe': 'http://www.portalfiscal.inf.br/nfe'
    }

    def _get_text(self, root, path: str) -> Optional[str]:
        """Helper para extrair texto de um elemento ignorando namespaces totalmente."""
        try:
            # Constrói caminho xpath ignorando namespaces
            # Ex: "ide/nNF" -> ".//*[local-name()='ide']/*[local-name()='nNF']"
            parts = path.split("/")
            xpath_expr = ".//" + "/".join([f"*[local-name()='{p}']" for p in parts])
            
            elements = root.xpath(xpath_expr)
            if elements:
                return elements[0].text
            
            return None
        except Exception as e:
            logger.warning(f"Erro ao extrair {path}: {str(e)}")
            return None

    def parse_nfe(self, xml_content: bytes) -> Dict[str, Any]:
        """
        Processa o XML bruto e retorna um dicionário estruturado de forma ultra-resiliente.
        """
        try:
            # Segurança: Desabilitar resolução de entidades externas (Proteção contra XXE)
            parser = etree.XMLParser(
                recover=True, 
                remove_blank_text=True,
                resolve_entities=False, # Não resolve entidades (&entidade;)
                no_network=True,        # Bloqueia acesso à rede durante o parse
                dtd_validation=False,   # Ignora DTD maliciosos
                load_dtd=False          # Não carrega DTDs externos
            )
            root = etree.fromstring(xml_content, parser)
            
            if root is None:
                raise ValueError("Arquivo XML corrompido ou mal formatado.")

            # 1. Localizar infNFe de forma universal
            # Busca em qualquer nível um elemento cujo nome seja 'infNFe'
            inf_nfe_elements = root.xpath("//*[local-name()='infNFe']")
            
            if inf_nfe_elements:
                root = inf_nfe_elements[0]
            elif not (root.tag.endswith('infNFe') or 'infNFe' in root.tag):
                # Se não achou via XPath e o raiz também não é, falhou
                logger.error(f"Estrutura NFe inválida. Tag Raiz: {root.tag}. Snippet: {xml_content[:100].decode('utf-8', 'ignore')}")
                raise ValueError("Estrutura de NF-e inválida: infNFe não encontrada.")
            
            # Se chegou aqui, root é o infNFe ou o elemento que o contém (se o else acima não pegou)
            # Garantir que temos o ID da nota (Chave de Acesso)
            chave = root.get('Id')
            if not chave:
                # Tenta buscar Id em níveis superiores se root for um descendente
                chave = root.xpath("ancestor-or-self::*[local-name()='infNFe']/@Id")
                chave = chave[0] if chave else None

            # Extração de Dados utilizando o helper ultra-resiliente
            dados = {
                "chave_acesso": chave.replace('NFe', '') if chave else None,
                "numero": self._get_text(root, "ide/nNF"),
                "serie": self._get_text(root, "ide/serie"),
                "data_emissao": self._get_text(root, "ide/dhEmi") or self._get_text(root, "ide/dEmi"),
                
                # Emitente / Destinatário
                "emitente_cnpj": self._get_text(root, "emit/CNPJ") or self._get_text(root, "emit/CPF"),
                "emitente_nome": self._get_text(root, "emit/xNome"),
                "emitente_uf": (
                    self._get_text(root, "emit/enderEmit/UF") or
                    self._get_text(root, "ide/cUF")
                ),
                "destinatario_cnpj": self._get_text(root, "dest/CNPJ") or self._get_text(root, "dest/CPF"),
                "destinatario_nome": self._get_text(root, "dest/xNome"),
                "destinatario_uf": self._get_text(root, "dest/enderDest/UF"),
                
                # Valores Totais
                "valor_total": float(self._get_text(root, "total/ICMSTot/vNF") or 0.0),
                
                # Campos da Reforma (CBS/IBS)
                "valor_cbs": float(self._get_text(root, "total/vCBS") or 0.0), 
                "valor_ibs": float(self._get_text(root, "total/vIBS") or 0.0), 
                
                "itens": []
            }

            # Extrair Itens para análise granular (NCM, CFOP, CST por item)
            det_elements = root.xpath(".//*[local-name()='det']")
            for det in det_elements:
                item = {
                    "n_item": int(det.get("nItem") or 0),
                    "x_prod": self._get_text(det, "prod/xProd"),
                    "ncm": self._get_text(det, "prod/NCM"),
                    "cfop": self._get_text(det, "prod/CFOP"),
                    "cst": (
                        self._get_text(det, "imposto/ICMS/ICMS00/CST") or
                        self._get_text(det, "imposto/ICMS/ICMS10/CST") or
                        self._get_text(det, "imposto/ICMS/ICMS20/CST") or
                        self._get_text(det, "imposto/ICMS/ICMS60/CST") or
                        self._get_text(det, "imposto/ICMS/ICMSSN101/CSOSN") or
                        self._get_text(det, "imposto/ICMS/ICMSSN102/CSOSN")
                    ),
                    "v_prod": float(self._get_text(det, "prod/vProd") or 0.0),
                    # Campos da Reforma
                    "v_cbs": float(self._get_text(det, "imposto/vCBS") or 0.0),
                    "v_ibs": float(self._get_text(det, "imposto/vIBS") or 0.0),
                    # Tributos Vigentes (Legado)
                    "v_pis": float(
                        self._get_text(det, "imposto/PIS/PISAliq/vPIS") or 
                        self._get_text(det, "imposto/PIS/PISOutr/vPIS") or 0.0
                    ),
                    "v_cofins": float(
                        self._get_text(det, "imposto/COFINS/COFINSAliq/vCOFINS") or 
                        self._get_text(det, "imposto/COFINS/COFINSOutr/vCOFINS") or 0.0
                    ),
                    "v_icms": float(
                        self._get_text(det, "imposto/ICMS/ICMS00/vICMS") or 
                        self._get_text(det, "imposto/ICMS/ICMS10/vICMS") or 
                        self._get_text(det, "imposto/ICMS/ICMS20/vICMS") or 
                        self._get_text(det, "imposto/ICMS/ICMS70/vICMS") or 
                        self._get_text(det, "imposto/ICMS/ICMS90/vICMS") or 0.0
                    ),
                }
                dados["itens"].append(item)

            return dados

        except etree.XMLSyntaxError:
            raise ValueError("Arquivo XML corrompido ou mal formatado.")
        except Exception as e:
            logger.error(f"Erro no parsing: {str(e)}")
            raise e
