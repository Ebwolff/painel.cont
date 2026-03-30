import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn } from 'typeorm';
import { Empresa } from './empresa.entity';

export enum StatusManifestacao {
  PENDENTE = 'pendente',
  AGUARDANDO_XML = 'aguardando_xml',
  COMPLETO = 'completo',
  ERRO = 'erro'
}

@Entity('notas_fiscais')
export class NotaFiscal {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column('uuid')
  empresa_id: string;

  @Column({ unique: true })
  chave: string;

  @Column()
  nsu: string;

  @Column({ nullable: true })
  xml_url: string;

  @Column({ nullable: true })
  emitente: string;

  @Column({ nullable: true })
  destinatario: string;

  @Column('decimal', { precision: 12, scale: 2, default: 0 })
  valor_total: number;

  @Column({ nullable: true })
  cfop: string;

  @Column({ type: 'timestamp', nullable: true })
  data_emissao: Date;

  @Column({ type: 'enum', enum: StatusManifestacao, default: StatusManifestacao.PENDENTE })
  status_manifestacao: StatusManifestacao;

  @ManyToOne(() => Empresa)
  @JoinColumn({ name: 'empresa_id' })
  empresa: Empresa;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;
}
