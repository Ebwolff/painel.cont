import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { NotaFiscal, StatusManifestacao } from './entities/nota-fiscal.entity';
import * as zlib from 'zlib';
import { XMLParser } from 'fast-xml-parser';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

@Injectable()
export class NfeService {
  private readonly logger = new Logger(NfeService.name);
  private readonly s3Client: S3Client;

  constructor(
    @InjectRepository(NotaFiscal)
    private notaFiscalRepository: Repository<NotaFiscal>
  ) {
    this.s3Client = new S3Client({
      region: process.env.AWS_REGION || 'us-east-1',
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
      }
    });
  }

  /**
   * Descompacta XML retornado em Base64 GZip pela SEFAZ
   */
  private extractXml(base64Gz: string): string {
    const buffer = Buffer.from(base64Gz, 'base64');
    const unzipped = zlib.gunzipSync(buffer);
    return unzipped.toString('utf-8');
  }

  /**
   * Processa o Documento (resNFe, procNFe)
   */
  async processarDocumentoSefaz(doc: any, empresaId: string) {
    const xml = this.extractXml(doc.xmlGzBase64);
    
    // Parse via fast-xml-parser
    const parser = new XMLParser({ ignoreAttributes: false });
    const parsed = parser.parse(xml);

    let chave = '';
    let statusManifestacao = StatusManifestacao.PENDENTE;
    let s3Url = null;

    if (doc.tipoDoc === 'resNFe') {
      chave = parsed.resNFe.chNFe;
      statusManifestacao = StatusManifestacao.AGUARDANDO_XML;
    } else if (doc.tipoDoc === 'procNFe') {
      chave = parsed.nfeProc.protNFe.infProt.chNFe;
      statusManifestacao = StatusManifestacao.COMPLETO;
      
      // Envia XML Completo para o S3
      s3Url = await this.uploadToS3(`xmls/${empresaId}/${chave}.xml`, xml);
    }

    // Salvar no Banco
    const nota = this.notaFiscalRepository.create({
      empresa_id: empresaId,
      nsu: doc.nsu,
      chave: chave,
      status_manifestacao: statusManifestacao,
      xml_url: s3Url,
      // Extrair emitente, cnpj, valor através do \`parsed\`
      emitente: doc.tipoDoc === 'resNFe' ? parsed.resNFe.xNome : parsed.nfeProc.NFe.infNFe.emit.xNome,
      valor_total: doc.tipoDoc === 'resNFe' ? parseFloat(parsed.resNFe.vNF) : parseFloat(parsed.nfeProc.NFe.infNFe.total.ICMSTot.vNF),
      data_emissao: doc.tipoDoc === 'resNFe' ? new Date(parsed.resNFe.dhEmi) : new Date(parsed.nfeProc.NFe.infNFe.ide.dhEmi)
    });

    try {
      await this.notaFiscalRepository.upsert(nota, ['chave']);
      this.logger.log(`Nota ${chave} armazenada com sucesso.`);
    } catch (e: any) {
       this.logger.error(`Duplicidade ou erro no DB para nota ${chave}`);
    }
  }

  private async uploadToS3(key: string, content: string): Promise<string> {
    const bucket = process.env.AWS_S3_BUCKET || 'nfe-s3-bucket';
    const command = new PutObjectCommand({
      Bucket: bucket,
      Key: key,
      Body: content,
      ContentType: 'application/xml'
    });
    
    await this.s3Client.send(command);
    return \`https://\${bucket}.s3.amazonaws.com/\${key}\`;
  }
}
