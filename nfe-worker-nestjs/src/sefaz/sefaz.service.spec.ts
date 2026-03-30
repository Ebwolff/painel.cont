import { Test, TestingModule } from '@nestjs/testing';
import { SefazService } from './sefaz.service';

describe('SefazService', () => {
  let service: SefazService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [SefazService],
    }).compile();

    service = module.get<SefazService>(SefazService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
