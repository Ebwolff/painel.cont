import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Empresa } from '../nfe/entities/empresa.entity';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { NFE_QUEUE } from '../nfe/nfe.processor';

@Injectable()
export class SchedulerService {
  private readonly logger = new Logger(SchedulerService.name);

  constructor(
    @InjectRepository(Empresa)
    private empresaRepository: Repository<Empresa>,
    @InjectQueue(NFE_QUEUE) private nfeQueue: Queue
  ) {}

  /**
   * Executa a cada 5 minutos
   * Busca todas as empresas que têm certificado válido e agenda o job
   */
  @Cron(CronExpression.EVERY_5_MINUTES)
  async scheduleNfeConsultation() {
    this.logger.log('Iniciando Schedule de Consulta de NF-e...');
    
    // Na prática, buscaria na DB empresas "ativas" e com certificados ainda no prazo
    // Aqui usamos uma query genérica
    const empresas = await this.empresaRepository.find();

    for (const empresa of empresas) {
      this.logger.debug(`Agendando job para empresa ${empresa.id}.`);
      
      // Adiciona o job à fila configurando Exponential Backoff (regra da OPÇÃO 1)
      await this.nfeQueue.add('consultar-dfe', {
        empresaId: empresa.id,
        nsu: empresa.ultimo_nsu,
      }, {
        attempts: 6, // 1 tentativa + 5 retries
        backoff: {
          type: 'exponential',
          delay: 5 * 60 * 1000, // Começa tentando em 5 minutos (1000 * 60 * 5)
        },
        removeOnComplete: true, // Auto-limpeza do redis
        removeOnFail: false
      });
    }

    this.logger.log(`Foram agendados ${empresas.length} jobs para consulta na SEFAZ.`);
  }
}
