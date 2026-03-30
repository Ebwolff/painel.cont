import { Module } from '@nestjs/common';
import { SchedulerService } from './scheduler.service';
import { NfeModule } from '../nfe/nfe.module';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Empresa } from '../nfe/entities/empresa.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Empresa]), NfeModule],
  providers: [SchedulerService],
})
export class SchedulerModule {}
