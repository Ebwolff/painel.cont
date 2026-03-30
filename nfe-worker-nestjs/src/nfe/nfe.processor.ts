import { Processor, WorkerHost, OnWorkerEvent } from '@nestjs/bullmq';
import { Job } from 'bullmq';
import { Logger } from '@nestjs/common';
import { NfeService } from './nfe.service';
import { SefazService } from '../sefaz/sefaz.service';
import { CertificadoService } from '../certificado/certificado.service';
import { Empresa } from './entities/empresa.entity';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

export const NFE_QUEUE = 'nfe-consulta';

@Processor(NFE_QUEUE, {
  concurrency: 5,
  limiter: { max: 10, duration: 1000 }
})
export class NfeProcessor extends WorkerHost {
  private readonly logger = new Logger(NfeProcessor.name);

  constructor(
    private nfeService: NfeService,
    private sefazService: SefazService,
    private certificadoService: CertificadoService,
    @InjectRepository(Empresa)
    private empresaRepository: Repository<Empresa>
  ) {
    super();
  }

  async process(job: Job<any, any, string>): Promise<any> {
    this.logger.log(`Iniciando Job ${job.name} -> ID: ${job.id}`);
    
    if (job.name === 'consultar-dfe') {
        return this.processarConsultaDFe(job);
    } else if (job.name === 'consultar-chave-repescagem') {
        return this.processarConsultaPorChave(job);
    }
  }

  async processarConsultaDFe(job: Job) {
    const { empresaId, nsu } = job.data;
    const empresa = await this.empresaRepository.findOne({ where: { id: empresaId } });
    if (!empresa) throw new Error('Empresa não encontrada');
    
    const certData = await this.certificadoService.getCertificado(empresaId);
    if (!certData) throw new Error('Certificado não encontrado/inválido');

    const documentos = await this.sefazService.consultarDistribuicao(
      empresa.cnpj, 
      nsu || empresa.ultimo_nsu,
      certData.certPem,
      certData.keyPem
    );

    let maxNsuRetornado = empresa.ultimo_nsu;

    for (const doc of documentos) {
      try {
        await this.nfeService.processarDocumentoSefaz(doc, empresa.id);
        if (BigInt(doc.nsu) > BigInt(maxNsuRetornado)) maxNsuRetornado = doc.nsu;
      } catch (err: any) {
        this.logger.error(`Erro ao salvar doc NSU ${doc.nsu}: ${err.message}`);
      }
    }

    if (maxNsuRetornado !== empresa.ultimo_nsu) {
      empresa.ultimo_nsu = maxNsuRetornado;
      await this.empresaRepository.save(empresa);
    }

    return { nsuAnterior: nsu, nsuNovo: maxNsuRetornado };
  }

  async processarConsultaPorChave(job: Job) {
      const { empresaId, chave } = job.data;
      const certData = await this.certificadoService.getCertificado(empresaId);
      if (!certData) throw new Error('Certificado não encontrado/inválido');
      
      try {
          const xmlCompletoAutorizado = await this.sefazService.consultarPorChave(chave, certData.certPem, certData.keyPem);
          
          // O processo deu certo. Extraímos o procNFe do XML, geramos um doc compatível e chamamos o parse regular.
          // Como é "Option 1 - Código pronto arquitetural", encapsulamos via DFe mock estrutural
          const mockDoc = {
              nsu: null,
              schema: '',
              xmlGzBase64: Buffer.from(xmlCompletoAutorizado).toString('base64'),
              tipoDoc: 'procNFe' // Força marcação de arquivo base completo
          };

          await this.nfeService.processarDocumentoSefaz(mockDoc, empresaId);

      } catch (err: any) {
          if (err.message === 'NOTA_NAO_ENCONTRADA_AINDA') {
             // O erro dispara o exponential backoff nativo do BullMQ da repescagem (1h, 6h, etc).
             throw err;
          }
          this.logger.error(`Erro crítico na repescagem: ${err.message}`);
          throw err;
      }
  }

  @OnWorkerEvent('failed')
  async onWorkerFailed(job: Job, error: Error) {
    this.logger.error(`Job [${job.id}] failed with error: ${error.message}`);
    // Se o job esgotou todas as tentativas (ex: atingiu as 48h limitadas via attempts + backoff array custom)
    if (job.name === 'consultar-chave-repescagem' && job.opts?.attempts && job.attemptsMade >= job.opts.attempts) {
        this.logger.warn(`Desistindo da repescagem para a chave ${job.data.chave}. Marcando status para NAO_ENCONTADA.`);
        await this.nfeService.setNotaDesconhecida(job.data.empresaId, job.data.chave);
    }
  }
}
