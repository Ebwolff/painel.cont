import { Injectable, Logger } from '@nestjs/common';
import axios from 'axios';
import * as https from 'https';

export interface DistDfeResponse {
    nsu: string;
    schema: string;
    xmlGzBase64: string;
    tipoDoc: string; // 'resNFe', 'procNFe', 'resEvento' ...
}

@Injectable()
export class SefazService {
    private readonly logger = new Logger(SefazService.name);
    
    // NFeDistribuicaoDFe Endpoint Ambiente Nacional
    private readonly WS_URL = 'https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx';

    /**
     * Consulta o serviço de Distribuição DF-e da SEFAZ
     */
    async consultarDistribuicao(cnpj: string, ultimoNSU: string, certPem: string, keyPem: string) {
        this.logger.log(`Consultando DF-e para o CNPJ ${cnpj} a partir do NSU ${ultimoNSU}`);
        
        // Padrão de tamanho 15: ex "000000000000000"
        const paramNSU = ultimoNSU.padStart(15, '0');
        
        // Body XML da requisição
        const xmlBody = `<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Header>
    <nfeCabecMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
      <cUFAutor>35</cUFAutor>
      <versaoDados>1.38</versaoDados>
    </nfeCabecMsg>
  </soap12:Header>
  <soap12:Body>
    <nfeDistDFeInteresse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
      <nfeDadosMsg>
        <distDFeInt xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.38">
          <tpAmb>1</tpAmb>
          <cUFAutor>35</cUFAutor>
          <CNPJ>${cnpj}</CNPJ>
          <distNSU>
            <ultNSU>${paramNSU}</ultNSU>
          </distNSU>
        </distDFeInt>
      </nfeDadosMsg>
    </nfeDistDFeInteresse>
  </soap12:Body>
</soap12:Envelope>`;

        // Agent HTTPS utilizando o certificado A1 (mútuo TLS)
        const httpsAgent = new https.Agent({
            cert: certPem,
            key: keyPem,
            rejectUnauthorized: false,
        });

        try {
            const response = await axios.post(this.WS_URL, xmlBody, {
                headers: {
                    'Content-Type': 'application/soap+xml; charset=utf-8',
                    'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse'
                },
                httpsAgent,
                timeout: 30000 // 30s timeout para SEFAZ
            });

            // Extração Raw do payload ZIP retornado
            return this.parseDistDfeResponse(response.data);
        } catch (error: any) {
            this.logger.error(`Erro SEFAZ DistDFe: ${error.message}`);
            throw error;
        }
    }

    /**
     * Envia Manifestação do Destinatário (Ex: Ciência da Operação)
     */
    async manifestarNota(chave: string, tipoManifestacao: string, cnpj: string, certPem: string, keyPem: string) {
        this.logger.log(`Enviando Manifestação ${tipoManifestacao} para nota ${chave} (CNPJ: ${cnpj})`);
        
        // TODO: Assinar XML digitalmente (XML-DSIG) usando xml-crypto e a chave \`keyPem\`
        // Enviar SOAP request para evento NFeRecepcaoEvento4
        return true;
    }

    private parseDistDfeResponse(responseXml: string): DistDfeResponse[] {
        // Implementar uso de fast-xml-parser para validar retNFeDistDFeInt
        // Retorna status, lista de docs (docZip) e maxNSU.
        // Aqui é apenas o esqueleto (conforme solicitado Option 1)
        return [];
    }
}
