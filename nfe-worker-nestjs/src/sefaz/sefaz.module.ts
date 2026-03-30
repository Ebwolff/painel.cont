import { Module } from '@nestjs/common';
import { SefazService } from './sefaz.service';

@Module({
  providers: [SefazService],
  exports: [SefazService],
})
export class SefazModule {}
