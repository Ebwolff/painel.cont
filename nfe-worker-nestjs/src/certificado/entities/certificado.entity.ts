import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn } from 'typeorm';
import { Empresa } from '../../nfe/entities/empresa.entity';

@Entity('certificados')
export class Certificado {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column('uuid')
  empresa_id: string;

  @Column()
  caminho_arquivo: string; // Caminho no S3

  @Column()
  senha_criptografada: string;

  @Column('timestamp')
  validade: Date;

  @ManyToOne(() => Empresa)
  @JoinColumn({ name: 'empresa_id' })
  empresa: Empresa;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;
}
