"""
Assinatura digital XMLDSIG para eventos SEFAZ.
Padrão atual: SHA-1 (exigido pela SEFAZ).
Preparado para migração futura para SHA-256.

Usa: lxml + xmlsec (requer libxmlsec1-dev no container).
"""
import xmlsec
from lxml import etree
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import logging

logger = logging.getLogger(__name__)

# Perfis de assinatura suportados
SIGN_PROFILES = {
    "sha1": {
        "sign_method": xmlsec.constants.TransformRsaSha1,
        "digest_method": xmlsec.constants.TransformSha1,
    },
    "sha256": {
        "sign_method": xmlsec.constants.TransformRsaSha256,
        "digest_method": xmlsec.constants.TransformSha256,
    },
}


class XMLSigner:
    """
    Assina XML com certificado A1 (PFX) usando Enveloped Signature.
    Compatível com ICP-Brasil e padrão SEFAZ.
    """

    def __init__(self, pfx_bytes: bytes, password: str, profile: str = "sha1"):
        """
        Args:
            pfx_bytes: Conteúdo binário do arquivo .pfx
            password: Senha do certificado
            profile: "sha1" (padrão SEFAZ atual) ou "sha256" (futuro)
        """
        pw = password.encode("utf-8") if isinstance(password, str) else password
        self.private_key, self.certificate, self.chain = load_key_and_certificates(pfx_bytes, pw)

        if profile not in SIGN_PROFILES:
            raise ValueError(f"Perfil '{profile}' inválido. Use: {list(SIGN_PROFILES.keys())}")
        self.profile = SIGN_PROFILES[profile]

    def sign_event(self, xml_element: etree._Element, reference_id: str) -> etree._Element:
        """
        Assina um elemento <evento> com Enveloped Signature.

        Args:
            xml_element: Elemento XML <evento> a ser assinado
            reference_id: Atributo Id do <infEvento> (ex: "ID210210...")

        Returns:
            Elemento XML com <Signature> inserido
        """
        # 1. Template de assinatura (perfil configurável)
        sig_node = xmlsec.template.create(
            xml_element,
            c14n_method=xmlsec.constants.TransformExclC14N,
            sign_method=self.profile["sign_method"],
            ns="ds",
        )

        # 2. Reference → aponta para o Id do infEvento
        ref = xmlsec.template.add_reference(
            sig_node,
            digest_method=self.profile["digest_method"],
            uri=f"#{reference_id}",
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformExclC14N)

        # 3. KeyInfo → X509Data com certificado
        key_info = xmlsec.template.ensure_key_info(sig_node)
        x509_data = xmlsec.template.add_x509_data(key_info)
        xmlsec.template.x509_data_add_certificate(x509_data)

        # 4. Inserir Signature no XML
        xml_element.append(sig_node)

        # 5. Carregar chave privada + certificado em memória
        cert_pem = self.certificate.public_bytes(Encoding.PEM)
        key_pem = self.private_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        )

        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(key_pem, xmlsec.constants.KeyDataFormatPem)
        ctx.key.load_cert(cert_pem, xmlsec.constants.KeyDataFormatPem)

        # 6. Assinar
        ctx.sign(sig_node)
        logger.debug(f"XML assinado com sucesso (ref={reference_id})")

        return xml_element
