import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Certificado } from './entities/certificado.entity';
import * as crypto from 'crypto';

@Injectable()
export class CertificadoService {
  private readonly logger = new Logger(CertificadoService.name);
  private readonly encryptionKey: Buffer;

  constructor(
    @InjectRepository(Certificado)
    private certificadoRepository: Repository<Certificado>
  ) {
    const key = process.env.CERTIFICATE_ENCRYPTION_KEY || 'default_key_32_bytes_long_string_';
    this.encryptionKey = Buffer.from(key.padEnd(32, '0').substring(0, 32));
  }

  encryptPassword(password: string): string {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', this.encryptionKey, iv);
    let encrypted = cipher.update(password, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return `${iv.toString('hex')}:${encrypted}`;
  }

  decryptPassword(encryptedPasswordHash: string): string {
    const parts = encryptedPasswordHash.split(':');
    const iv = Buffer.from(parts.shift() || '', 'hex');
    const encryptedText = parts.join(':');
    const decipher = crypto.createDecipheriv('aes-256-cbc', this.encryptionKey, iv);
    let decrypted = decipher.update(encryptedText, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
  }

  async getCertificado(empresaId: string): Promise<{ certPem: string, keyPem: string } | null> {
    const certificado = await this.certificadoRepository.findOne({ where: { empresa_id: empresaId } });
    if (!certificado) return null;

    if (new Date() > certificado.validade) {
      this.logger.error(`Certificado da empresa ${empresaId} expirou!`);
      throw new Error('Certificado expirado');
    }

    // A lógica de PFX -> PEM (node-forge) ficaria aqui extraindo de um storage.
    return { certPem: 'mock_cert', keyPem: 'mock_key' }; 
  }
}
