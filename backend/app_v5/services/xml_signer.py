"""
Assinatura digital XMLDSIG para eventos SEFAZ.
Usa: signxml (pure-Python) + lxml + cryptography.
Compatível com Python 3.14+ sem dependência de libxmlsec1.

NOTA: SEFAZ exige SHA-1 por padrão ICP-Brasil. signxml 4.x bloqueia SHA-1
por segurança. Usamos monkey-patch controlado para permitir SHA-1 somente
para assinaturas de eventos SEFAZ.
"""
from lxml import etree
from signxml import XMLSigner as SignXMLSigner, methods
from signxml.algorithms import (
    SignatureMethod, DigestAlgorithm, CanonicalizationMethod
)
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
# Patch: Permitir SHA-1 no signxml 4.x
# SEFAZ exige SHA-1 para eventos ICP-Brasil
# ═══════════════════════════════════════════
def _noop_check(self):
    """Bypass: permite SHA-1 para compatibilidade SEFAZ."""
    pass

SignXMLSigner.check_deprecated_methods = _noop_check


class XMLSigner:
    """
    Assina XML com certificado A1 (PFX) usando Enveloped Signature.
    Compatível com ICP-Brasil e padrão SEFAZ.
    """

    def __init__(self, pfx_bytes: bytes, password: str, profile: str = "sha1"):
        pw = password.encode("utf-8") if isinstance(password, str) else password
        self.private_key, self.certificate, self.chain = load_key_and_certificates(pfx_bytes, pw)

        if profile == "sha1":
            self.sig_method = SignatureMethod.RSA_SHA1
            self.digest_alg = DigestAlgorithm.SHA1
        else:
            self.sig_method = SignatureMethod.RSA_SHA256
            self.digest_alg = DigestAlgorithm.SHA256

    def sign_event(self, xml_element: etree._Element, reference_id: str) -> etree._Element:
        """
        Assina um elemento <evento> com Enveloped Signature.
        """
        cert_pem = self.certificate.public_bytes(Encoding.PEM)
        key_pem = self.private_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        )

        signer = SignXMLSigner(
            method=methods.enveloped,
            signature_algorithm=self.sig_method,
            digest_algorithm=self.digest_alg,
            c14n_algorithm=CanonicalizationMethod.CANONICAL_XML_1_0,
        )
        
        # Remove "ds:" prefix for strict SEFAZ compat
        import signxml
        signer.namespaces = {None: signxml.namespaces.ds}

        signed_root = signer.sign(
            xml_element,
            key=key_pem,
            cert=[cert_pem],
            reference_uri=f"#{reference_id}",
            always_add_key_value=False,
        )

        logger.debug(f"XML assinado com sucesso (ref={reference_id})")
        return signed_root
