import { Controller, Post, Body, Get, Param, HttpException, HttpStatus } from '@nestjs/common';
import { NfeService } from './nfe.service';
import { SefazService } from '../sefaz/sefaz.service';
import { CertificadoService } from '../certificado/certificado.service';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { NFE_QUEUE } from './nfe.processor';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { NotaFiscal, StatusManifestacao } from './entities/nota-fiscal.entity';

@Controller('nfe')
export class NfeController {
  constructor(
    private readonly nfeService: NfeService,
    private readonly sefazService: SefazService,
    private readonly certificadoService: CertificadoService,
    @InjectQueue(NFE_QUEUE) private readonly nfeQueue: Queue,
    @InjectRepository(NotaFiscal) private notaFiscalRepository: Repository<NotaFiscal>
  ) {}

  @Post('consultar-chave')
  async consultarPorChave(@Body() body: { empresaId: string, chave: string }) {
    const { empresaId, chave } = body;

    // 1. Verifica se já baixamos a nota completamente (Idempotência Limpa)
    const existing = await this.notaFiscalRepository.findOne({ where: { chave, empresa_id: empresaId } });
    if (existing && existing.status_manifestacao === StatusManifestacao.COMPLETO) {
        return { status: 'success', message: 'Nota já estava disponível e processada no banco local.', nota: existing };
    }

    const certData = await this.certificadoService.getCertificado(empresaId);
    if (!certData) throw new HttpException('Certificado não configurado.', HttpStatus.BAD_REQUEST);

    // 2. Tentativa 1 (Imediata / Síncrona)
    try {
        const xmlCompletoAutorizado = await this.sefazService.consultarPorChave(chave, certData.certPem, certData.keyPem);
        
        // Sucesso na primeira tentativa! Simula payload DistDFe para ser engolido pelo parser natural da Option 1.
        const mockDoc = {
            nsu: null,
            schema: '',
            xmlGzBase64: Buffer.from(xmlCompletoAutorizado).toString('base64'),
            tipoDoc: 'procNFe'
        };
        await this.nfeService.processarDocumentoSefaz(mockDoc, empresaId);

        return { status: 'success', message: 'Nota consultada e salva com sucesso!' };

    } catch (e: any) {
        if (e.message === 'NOTA_NAO_ENCONTRADA_AINDA') {
            // 3. Coloca na Fila de Repescagem com Backoff Exponencial
            // Agenda as próximas 4 tentativas para fechar as 5 (15m, 1h, 6h, 24h)
            // O algoritmo de exponential usando power de base 4: delay inicial 15m
            await this.nfeQueue.add('consultar-chave-repescagem', { empresaId, chave }, {
                attempts: 4, 
                backoff: {
                    type: 'exponential',
                    delay: 15 * 60 * 1000 // 15 minutos
                },
                removeOnComplete: true,
            });

            throw new HttpException({
                status: 'pending_sefaz',
                message: 'A nota foi localizada, mas ainda não está disponível no ambiente nacional da SEFAZ. Tente novamente em alguns minutos.'
            }, HttpStatus.UNPROCESSABLE_ENTITY); // 422
        }

        // Outros erros síncronos
        throw new HttpException(e.message, HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  @Post('sincronizar')
  async sincronizarDFeGeral(@Body() body: { empresaId: string }) {
      // Dispara a rotina manual da NFe DistDFe fora do cron schedule
      await this.nfeQueue.add('consultar-dfe', { empresaId: body.empresaId }, {
          attempts: 1, removeOnComplete: true
      });
      return { message: 'Sincronização global da SEFAZ enfileirada com sucesso!' };
  }

  @Get()
  async listarNotas() {
      // Paginação real viria aqui. Apenas demonstração.
      return this.notaFiscalRepository.find({ take: 50, order: { created_at: 'DESC' } });
  }

  @Get(':id')
  async obterNota(@Param('id') id: string) {
      return this.notaFiscalRepository.findOneOrFail({ where: { id } });
  }
}
