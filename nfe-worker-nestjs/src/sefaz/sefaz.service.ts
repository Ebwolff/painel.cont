import { Injectable, Logger } from '@nestjs/common';
import axios from 'axios';
import * as https from 'https';

export interface DistDfeResponse {
    nsu: string;
    schema: string;
    xmlGzBase64: string;
    tipoDoc: string; // 'resNFe', 'procNFe', 'resEvento'
}

@Injectable()
export class SefazService {
    private readonly logger = new Logger(SefazService.name);
    
    // NFeDistribuicaoDFe Endpoint Ambiente Nacional
    private readonly WS_DIST_URL = 'https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx';
    // NFeConsultaProtocolo Endpoint Ambiente Nacional (SVAN / SVRS dependem do estado, usando URL genérica como stub)
    private readonly WS_CONSULTA_URL = 'https://www1.nfe.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx';

    /**
     * Consulta o serviço de Distribuição DF-e da SEFAZ
     */
    async consultarDistribuicao(cnpj: string, ultimoNSU: string, certPem: string, keyPem: string) {
        this.logger.log(`Consultando DF-e para o CNPJ ${cnpj} a partir do NSU ${ultimoNSU}`);
        const paramNSU = ultimoNSU.padStart(15, '0');
        
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

        const httpsAgent = new https.Agent({ cert: certPem, key: keyPem, rejectUnauthorized: false });

        try {
            const response = await axios.post(this.WS_DIST_URL, xmlBody, {
                headers: {
                    'Content-Type': 'application/soap+xml; charset=utf-8',
                    'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse'
                },
                httpsAgent,
                timeout: 30000
            });
            return this.parseDistDfeResponse(response.data);
        } catch (error: any) {
            this.logger.error(`Erro SEFAZ DistDFe: ${error.message}`);
            throw error;
        }
    }

    /**
     * NFeConsultaProtocolo para Notas Emitidas
     * Retorna o XML Completo quando a chave estiver disponível
     */
    async consultarPorChave(chaveAcesso: string, certPem: string, keyPem: string): Promise<string> {
        this.logger.log(`Consultando NFe por chave: ${chaveAcesso}`);
        
        const xmlBody = `<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Header>
    <nfeCabecMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
      <cUFAutor>35</cUFAutor>
      <versaoDados>4.00</versaoDados>
    </nfeCabecMsg>
  </soap12:Header>
  <soap12:Body>
    <nfeConsultaNF xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
      <nfeDadosMsg>
        <consSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
          <tpAmb>1</tpAmb>
          <xServ>CONSULTAR</xServ>
          <chNFe>${chaveAcesso}</chNFe>
        </consSitNFe>
      </nfeDadosMsg>
    </nfeConsultaNF>
  </soap12:Body>
</soap12:Envelope>`;

        const httpsAgent = new https.Agent({ cert: certPem, key: keyPem, rejectUnauthorized: false });

        try {
            const response = await axios.post(this.WS_CONSULTA_URL, xmlBody, {
                headers: {
                    'Content-Type': 'application/soap+xml; charset=utf-8',
                    'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4/nfeConsultaNF'
                },
                httpsAgent,
                timeout: 30000
            });

            // Se o retorno indicar CStat 100/150, significa que nota foi processada. 
            // Porém o ConsultaNFe retNFe não retorna o XML da NF-e bruta, 
            // ele retorna o procNFe do autorizativo. A Sefaz requer download avulso.
            // Para efeitos de abstração arquitetônica (SOAP RAW request):
            const xmlEncontrado = response.data; // string bruta do response
            
            // Simulação de check de CSTAT 422:
            if (xmlEncontrado.includes('<cStat>217</cStat>') || xmlEncontrado.includes('<cStat>656</cStat>') || xmlEncontrado.includes('Nao consta na base')) {
                throw new Error('NOTA_NAO_ENCONTRADA_AINDA');
            }

            return xmlEncontrado; // Em prod aplicamos parser p/ o proc xml final
        } catch (error: any) {
            this.logger.error(`Erro SEFAZ Consulta Protocolo [${chaveAcesso}]: ${error.message}`);
            throw error;
        }
    }

    async manifestarNota(chave: string, tipoManifestacao: string, cnpj: string, certPem: string, keyPem: string) {
        this.logger.log(`Enviando Manifestação ${tipoManifestacao} para nota ${chave} (CNPJ: ${cnpj})`);
        // Lógica de XML-DSIG com xml-crypto ficaria aqui
        return true;
    }

    private parseDistDfeResponse(responseXml: string): DistDfeResponse[] {
        return [];
    }
}
