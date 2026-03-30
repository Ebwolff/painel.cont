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
  concurrency: 5, // Controle de processamento simultâneo
  limiter: {
    max: 10,
    duration: 1000, 
  }
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
    this.logger.log(`Iniciando Job ${job.id} -> Empresa ${job.data.empresaId}`);

    const { empresaId } = job.data;
    const empresa = await this.empresaRepository.findOne({ where: { id: empresaId } });
    
    if (!empresa) {
      throw new Error('Empresa não encontrada');
    }

    const certData = await this.certificadoService.getCertificado(empresaId);
    if (!certData) {
      throw new Error('Certificado não encontrado/inválido');
    }

    // Consulta SEFAZ (distDFeInt)
    const documentos = await this.sefazService.consultarDistribuicao(
      empresa.cnpj, 
      empresa.ultimo_nsu,
      certData.certPem,
      certData.keyPem
    );

    let maxNsuRetornado = empresa.ultimo_nsu;

    // Processar cada documento
    for (const doc of documentos) {
      try {
        await this.nfeService.processarDocumentoSefaz(doc, empresa.id);
        if (BigInt(doc.nsu) > BigInt(maxNsuRetornado)) {
            maxNsuRetornado = doc.nsu;
        }
      } catch (err: any) {
        this.logger.error(`Erro ao salvar doc NSU ${doc.nsu}: ${err.message}`);
      }
    }

    // Atualiza NSU no banco para próxima iteração
    if (maxNsuRetornado !== empresa.ultimo_nsu) {
      empresa.ultimo_nsu = maxNsuRetornado;
      await this.empresaRepository.save(empresa);
    }

    return { nsuAnterior: job.data.nsu, nsuNovo: maxNsuRetornado, totalEncontrados: documentos.length };
  }

  @OnWorkerEvent('failed')
  onWorkerFailed(job: Job, error: Error) {
    this.logger.error(`Job [${job.id}] failed with error: ${error.message}`);
    // Exponential backoff rules configured when adding the job!
  }
}
