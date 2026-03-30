import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn, Index } from 'typeorm';
import { Empresa } from './empresa.entity';

export enum StatusManifestacao {
  PENDENTE = 'pendente',
  AGUARDANDO_XML = 'aguardando_xml',
  COMPLETO = 'completo',
  ERRO = 'erro',
  NAO_ENCONTRADA = 'nao_encontrada'
}

export enum TipoNota {
  EMITIDA = 'emitida',
  RECEBIDA = 'recebida'
}

@Entity('notas_fiscais')
@Index(['empresa_id', 'chave'], { unique: true }) // Constraint forte p/ concorrência
export class NotaFiscal {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column('uuid')
  empresa_id: string;

  @Column({ unique: true })
  chave: string;

  @Column({ nullable: true })
  nsu: string;

  @Column({ type: 'enum', enum: TipoNota, default: TipoNota.RECEBIDA })
  tipo: TipoNota;

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

  // Lock Lógico (Idempotência e Prevenção de Race Conditions)
  @Column({ type: 'boolean', default: false })
  processing: boolean;

  @ManyToOne(() => Empresa)
  @JoinColumn({ name: 'empresa_id' })
  empresa: Empresa;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;
}
