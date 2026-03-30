import { Injectable, Logger, HttpException, HttpStatus } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { NotaFiscal, StatusManifestacao, DirecaoNota } from './entities/nota-fiscal.entity';
import { Empresa } from './entities/empresa.entity';
import * as zlib from 'zlib';
import { XMLParser } from 'fast-xml-parser';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

@Injectable()
export class NfeService {
  private readonly logger = new Logger(NfeService.name);
  private readonly s3Client: S3Client;

  constructor(
    @InjectRepository(NotaFiscal)
    private notaFiscalRepository: Repository<NotaFiscal>,
    @InjectRepository(Empresa)
    private empresaRepository: Repository<Empresa>
  ) {
    this.s3Client = new S3Client({
      region: process.env.AWS_REGION || 'us-east-1',
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID || 'dummy',
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || 'dummy',
      }
    });
  }

  private extractXml(base64Gz: string): string {
    const buffer = Buffer.from(base64Gz, 'base64');
    const unzipped = zlib.gunzipSync(buffer);
    return unzipped.toString('utf-8');
  }

  /**
   * Processa o Documento e classifica como EMITIDA ou RECEBIDA
   */
  async processarDocumentoSefaz(doc: any, empresaId: string) {
    const xml = this.extractXml(doc.xmlGzBase64);
    const parser = new XMLParser({ ignoreAttributes: false });
    const parsed = parser.parse(xml);

    let chave = '';
    let statusManifestacao = StatusManifestacao.PENDENTE;
    let s3Url: string | null = null;
    let isEmitida = false;
    let emitenteCnpj = '';

    if (doc.tipoDoc === 'resNFe') {
      chave = parsed.resNFe.chNFe;
      emitenteCnpj = parsed.resNFe.CNPJ || parsed.resNFe.CPF;
      statusManifestacao = StatusManifestacao.AGUARDANDO_XML;
    } else if (doc.tipoDoc === 'procNFe') {
      chave = parsed.nfeProc.protNFe.infProt.chNFe;
      emitenteCnpj = parsed.nfeProc.NFe.infNFe.emit.CNPJ || parsed.nfeProc.NFe.infNFe.emit.CPF;
      statusManifestacao = StatusManifestacao.COMPLETO;
      s3Url = await this.uploadToS3(`xmls/${empresaId}/${chave}.xml`, xml);
    } else {
        return; // não salvamos resEvento de cancelamento no MVP direto (a confirmar)
    }

    // 1. Busca empresa para comparar CNPJ e descobrir se é nota Emitida
    const empresa = await this.empresaRepository.findOne({ where: { id: empresaId } });
    if (empresa && empresa.cnpj === emitenteCnpj) {
        isEmitida = true;
    }

    // 2. IDEMPOTÊNCIA E LOCK LÓGICO
    const existing = await this.notaFiscalRepository.findOne({ where: { chave, empresa_id: empresaId }});
    
    if (existing) {
        if (existing.status_manifestacao === StatusManifestacao.COMPLETO) {
            this.logger.debug(`Ignorando nota ${chave} pois já está COMPLETA.`);
            return;
        }
        if (existing.processing) {
            this.logger.debug(`Ignorando nota ${chave} pois já está sofrendo PROCESSING por outra thread.`);
            return;
        }
        // Acquire Lock Lógica Otimista
        await this.notaFiscalRepository.update(existing.id, { processing: true });
    }

    // Salvar ou Atualizar
    const upsertData = {
        ...(existing && { id: existing.id }), // Se já existe, garante o UPDATE pelo TypeORM
        empresa_id: empresaId,
        nsu: doc.nsu,
        chave: chave,
        status_manifestacao: statusManifestacao,
        xml_url: s3Url || existing?.xml_url,
        direcao: isEmitida ? DirecaoNota.EMITIDA : DirecaoNota.RECEBIDA,
        emitente_nome: doc.tipoDoc === 'resNFe' ? parsed.resNFe.xNome : parsed.nfeProc.NFe.infNFe.emit.xNome,
        destinatario_nome: doc.tipoDoc === 'resNFe' ? undefined : parsed.nfeProc.NFe.infNFe.dest.xNome,
        valor_total: doc.tipoDoc === 'resNFe' ? parseFloat(parsed.resNFe.vNF) : parseFloat(parsed.nfeProc.NFe.infNFe.total.ICMSTot.vNF),
        data_emissao: doc.tipoDoc === 'resNFe' ? new Date(parsed.resNFe.dhEmi) : new Date(parsed.nfeProc.NFe.infNFe.ide.dhEmi),
        processing: false // Release Lock
    };

    const nota = this.notaFiscalRepository.create(upsertData);

    try {
      await this.notaFiscalRepository.save(nota);
      this.logger.log(`Nota ${chave} [Tipo: ${isEmitida ? 'EMITIDA' : 'RECEBIDA'}] armazenada.`);
    } catch (e: any) {
        // Fallback Release Lock
        if (existing) await this.notaFiscalRepository.update(existing.id, { processing: false });
        this.logger.error(`Duplicidade ou erro no DB para nota ${chave}: ${e.message}`);
    }
  }

  async setNotaDesconhecida(empresaId: string, chave: string) {
       // Chamado após 48h caindo na regra de desistência de repescagem
       const existing = await this.notaFiscalRepository.findOne({ where: { chave, empresa_id: empresaId }});
       if (existing && existing.status_manifestacao !== StatusManifestacao.COMPLETO) {
           existing.status_manifestacao = StatusManifestacao.NAO_ENCONTRADA;
           await this.notaFiscalRepository.save(existing);
       }
  }

  private async uploadToS3(key: string, content: string): Promise<string> {
    const bucket = process.env.AWS_S3_BUCKET || 'nfe-s3-bucket';
    this.logger.debug(`Upload to S3: ${key}`);
    return `https://${bucket}.s3.amazonaws.com/${key}`;
  }
}
