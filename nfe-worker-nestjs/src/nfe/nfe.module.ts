import { Module } from '@nestjs/common';
import { NfeService } from './nfe.service';
import { NfeProcessor, NFE_QUEUE } from './nfe.processor';
import { BullModule } from '@nestjs/bullmq';
import { SefazModule } from '../sefaz/sefaz.module';
import { CertificadoModule } from '../certificado/certificado.module';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Empresa } from './entities/empresa.entity';
import { NotaFiscal } from './entities/nota-fiscal.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([Empresa, NotaFiscal]),
    BullModule.registerQueue({
      name: NFE_QUEUE,
    }),
    SefazModule,
    CertificadoModule
  ],
  providers: [NfeService, NfeProcessor],
  exports: [BullModule, TypeOrmModule], // Scheduler vai usar esse módulo e o TypeOrm
})
export class NfeModule {}
