import { Module } from '@nestjs/common';
import { CertificadoService } from './certificado.service';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Certificado } from './entities/certificado.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Certificado])],
  providers: [CertificadoService],
  exports: [CertificadoService],
})
export class CertificadoModule {}
