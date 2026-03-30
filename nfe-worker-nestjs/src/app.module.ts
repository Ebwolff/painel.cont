import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { BullModule } from '@nestjs/bullmq';
import { ScheduleModule } from '@nestjs/schedule';

import { AppController } from './app.controller';
import { AppService } from './app.service';

import { NfeModule } from './nfe/nfe.module';
import { CertificadoModule } from './certificado/certificado.module';
import { SefazModule } from './sefaz/sefaz.module';
import { SchedulerModule } from './scheduler/scheduler.module';

@Module({
  imports: [
    // Lê .env files globalmente
    ConfigModule.forRoot({ isGlobal: true }),

    // Conexão com PostgreSQL
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432', 10),
      username: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'secret',
      database: process.env.DB_NAME || 'saas_contabil',
      autoLoadEntities: true,
      synchronize: false, // Migrations são gerenciadas no projeto FastAPI principal
    }),

    // Conexão com Redis (BullMQ via ioredis)
    BullModule.forRoot({
      connection: {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT || '6379', 10),
        password: process.env.REDIS_PASSWORD || '',
      },
    }),

    // Cron jobs
    ScheduleModule.forRoot(),

    // Domínio Físcal
    CertificadoModule,
    SefazModule,
    NfeModule,
    SchedulerModule
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
