import React, { useEffect, useState, useCallback } from 'react';
import { Search, Filter, ArrowUpRight, ArrowDownLeft, FileText, CheckCircle2, AlertCircle, Calendar } from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../lib/utils';

export function MonitorFiscal() {
    const [loading, setLoading] = useState(true);
    const [notas, setNotas] = useState<any[]>([]);
    const [total, setTotal] = useState(0);
    const [companies, setCompanies] = useState<any[]>([]);
    const [filters, setFilters] = useState({
        empresa_id: '',
        direcao: 'entrada', // Default to Received
        status: '',
        search: '',
        dt_inicio: '',
        dt_fim: '',
        page: 1
    });

    const [rpaLoading, setRpaLoading] = useState(false);
    const [rpaMensagem, setRpaMensagem] = useState('');
    const [chaveRpa, setChaveRpa] = useState('');

    const handleTriggerRpa = async () => {
        if (!filters.empresa_id) {
            setRpaMensagem('Selecione uma empresa nos filtros.');
            return;
        }
        if (chaveRpa.length !== 44) {
            setRpaMensagem('A chave deve conter 44 dígitos.');
            return;
        }
        setRpaLoading(true);
        setRpaMensagem('');
        try {
            const res = await api.post(`/sefaz/rpa/sincronizar/${filters.empresa_id}?chave=${chaveRpa}`);
            setRpaMensagem(res.message || 'Robô acionado!');
            setChaveRpa('');
        } catch (error: any) {
            setRpaMensagem(error.response?.data?.detail || 'Erro ao acionar robô RPA.');
        } finally {
            setRpaLoading(false);
        }
    };


    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const queryParams = new URLSearchParams({
                page: filters.page.toString(),
                limit: '20'
            });
            if (filters.empresa_id) queryParams.append('empresa_id', filters.empresa_id);
            if (filters.direcao) queryParams.append('direcao', filters.direcao);
            if (filters.status) queryParams.append('status', filters.status);
            if (filters.search) queryParams.append('search', filters.search);
            if (filters.dt_inicio) queryParams.append('dt_inicio', filters.dt_inicio);
            if (filters.dt_fim) queryParams.append('dt_fim', filters.dt_fim);

            const [notasRes, companiesRes] = await Promise.all([
                api.get(`/notas/?${queryParams.toString()}`),
                api.get('/companies/')
            ]);

            setNotas(notasRes.data || []);
            setTotal(notasRes.total || 0);
            setCompanies(companiesRes || []);
        } catch (error) {
            console.error("Failed to fetch monitor data", error);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setFilters({ ...filters, page: 1 });
    };

    return (
        <div className="space-y-6">
            {/* Header & Controls */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white">Monitor Fiscal</h1>
                    <p className="text-sm text-end-text-sec">Histórico completo de documentos auditados via SEFAZ.</p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex bg-white/5 p-1 rounded-lg border border-white/5">
                        <button
                            onClick={() => setFilters({ ...filters, direcao: 'entrada', page: 1 })}
                            className={cn(
                                "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-bold transition-all",
                                filters.direcao === 'entrada' ? "bg-end-accent text-black" : "text-end-text-sec hover:text-white"
                            )}
                        >
                            <ArrowDownLeft size={14} /> Recebidas
                        </button>
                        <button
                            onClick={() => setFilters({ ...filters, direcao: 'saida', page: 1 })}
                            className={cn(
                                "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-bold transition-all",
                                filters.direcao === 'saida' ? "bg-end-accent text-black" : "text-end-text-sec hover:text-white"
                            )}
                        >
                            <ArrowUpRight size={14} /> Emitidas
                        </button>
                    </div>

                    <select
                        value={filters.empresa_id}
                        onChange={e => setFilters({ ...filters, empresa_id: e.target.value, page: 1 })}
                        className="bg-end-card border border-end-border text-end-text-sec text-xs font-bold py-2 px-3 rounded focus:outline-none focus:border-end-accent"
                    >
                        <option value="">Todas as Empresas</option>
                        {companies.map((c: any) => (
                            <option key={c.id} value={c.id}>{c.razao_social}</option>
                        ))}
                    </select>

                    <div className="flex items-center gap-2">
                        <input
                            type="date"
                            title="Data Inicial"
                            value={filters.dt_inicio}
                            onChange={e => setFilters({ ...filters, dt_inicio: e.target.value, page: 1 })}
                            className="bg-end-card border border-end-border text-end-text-sec text-xs py-2 px-2 rounded focus:outline-none focus:border-end-accent w-32"
                        />
                        <span className="text-end-text-sec text-xs">até</span>
                        <input
                            type="date"
                            title="Data Final"
                            value={filters.dt_fim}
                            onChange={e => setFilters({ ...filters, dt_fim: e.target.value, page: 1 })}
                            className="bg-end-card border border-end-border text-end-text-sec text-xs py-2 px-2 rounded focus:outline-none focus:border-end-accent w-32"
                        />
                    </div>

                    <form onSubmit={handleSearch} className="relative flex-grow min-w-[200px]">
                        <input
                            type="text"
                            placeholder="Número ou Chave..."
                            value={filters.search}
                            onChange={e => setFilters({ ...filters, search: e.target.value })}
                            className="bg-end-card border border-end-border text-white text-xs py-2 pl-9 pr-3 rounded focus:outline-none focus:border-end-accent w-full focus:w-full transition-all"
                        />
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-end-text-sec" size={14} />
                    </form>
                </div>
            </div>

            {/* RPA Trigger (Somente Emitidas) */}
            {filters.direcao === 'saida' && filters.empresa_id && (
                <div className="bg-end-card border border-end-accent/30 p-4 rounded-xl flex flex-col md:flex-row items-center gap-4 animate-fade-in shadow-[0_0_15px_rgba(255,255,255,0.05)]">
                    <div className="flex-1">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2"><ArrowUpRight size={16} className="text-end-accent" /> Extração RPA (Robô SEFAZ)</h3>
                        <p className="text-[10px] text-end-text-sec mt-1">
                            A SEFAZ bloqueia o Web Service para notas de <b>Emissão Própria</b>. Digite a chave de acesso abaixo para que o nosso Robô abra o Portal Nacional, resolva o Captcha e baixe o XML automaticamente.
                        </p>
                    </div>
                    <div className="flex flex-col md:flex-row items-center gap-3 w-full md:w-auto">
                        <input
                            type="text"
                            maxLength={44}
                            placeholder="Chave de Acesso (44 dígitos)"
                            value={chaveRpa}
                            onChange={e => setChaveRpa(e.target.value.replace(/\D/g, ''))}
                            className="bg-white/5 border border-white/10 text-white text-xs py-2 px-3 rounded focus:outline-none focus:border-end-accent w-full md:w-64 font-mono"
                        />
                        <button
                            onClick={handleTriggerRpa}
                            disabled={rpaLoading || chaveRpa.length !== 44}
                            className="bg-end-accent text-black px-4 py-2 rounded text-xs font-bold whitespace-nowrap disabled:opacity-50 hover:bg-end-accent/90 transition-all flex items-center justify-center gap-2 w-full md:w-auto"
                        >
                            {rpaLoading ? <span className="animate-spin">↻</span> : <CheckCircle2 size={14} />}
                            {rpaLoading ? 'Enviando...' : 'Iniciar Extração'}
                        </button>
                    </div>
                    {rpaMensagem && (
                        <p className={cn("text-[10px] font-bold mt-2 md:mt-0 max-w-[150px]", rpaMensagem.includes('Erro') || rpaMensagem.includes('Selecione') ? "text-end-error" : "text-end-success")}>
                            {rpaMensagem}
                        </p>
                    )}
                </div>
            )}

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-end-card border border-end-border p-4 rounded-xl">
                    <p className="text-[10px] font-black text-end-text-sec uppercase mb-1">Total {filters.direcao === 'entrada' ? 'Recebidas' : 'Emitidas'}</p>
                    <p className="text-2xl font-black text-white tracking-tighter">{total}</p>
                </div>
                <div className="bg-end-card border border-end-border p-4 rounded-xl">
                    <p className="text-[10px] font-black text-end-text-sec uppercase mb-1">Status SEFAZ</p>
                    <div className="flex items-center gap-2 mt-1">
                        <div className="w-2 h-2 rounded-full bg-end-success animate-pulse"></div>
                        <span className="text-sm font-bold text-white">Conexão Ativa</span>
                    </div>
                </div>
                <div className="bg-end-card border border-end-border p-4 rounded-xl">
                    <p className="text-[10px] font-black text-end-text-sec uppercase mb-1">Última Atualização</p>
                    <div className="flex items-center gap-2 mt-1">
                        <Calendar size={14} className="text-end-accent" />
                        <span className="text-sm font-bold text-white">Hoje, {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                </div>
            </div>

            {/* Table */}
            <div className="bg-end-card border border-end-border rounded-xl overflow-hidden shadow-2xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-white/5 border-b border-end-border">
                                <th className="p-4 text-[10px] font-bold text-end-text-sec uppercase tracking-widest">Nº/Série</th>
                                <th className="p-4 text-[10px] font-bold text-end-text-sec uppercase tracking-widest">Empresa</th>
                                <th className="p-4 text-[10px] font-bold text-end-text-sec uppercase tracking-widest">Valor</th>
                                <th className="p-4 text-[10px] font-bold text-end-text-sec uppercase tracking-widest">Emissão</th>
                                <th className="p-4 text-[10px] font-bold text-end-text-sec uppercase tracking-widest">Status Audit</th>
                                <th className="p-4 text-[10px] font-bold text-end-text-sec uppercase tracking-widest text-center">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-end-border">
                            {loading ? (
                                <tr><td colSpan={6} className="p-12 text-center text-end-text-sec animate-pulse">Consultando base SEFAZ...</td></tr>
                            ) : notas.length === 0 ? (
                                <tr><td colSpan={6} className="p-12 text-center text-end-text-sec italic">Nenhuma nota encontrada com estes filtros.</td></tr>
                            ) : notas.map((nota: any) => (
                                <tr key={nota.id} className="hover:bg-white/[0.02] transition-colors group">
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className={cn(
                                                "p-2 rounded-lg",
                                                filters.direcao === 'entrada' ? "bg-blue-500/10 text-blue-400" : "bg-end-accent/10 text-end-accent"
                                            )}>
                                                <FileText size={18} />
                                            </div>
                                            <div>
                                                <p className="text-sm font-black text-white">{nota.numero || '---'}</p>
                                                <p className="text-[10px] text-end-text-sec">Série {nota.serie || '001'}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <p className="text-sm font-bold text-white">{nota.empresas?.razao_social || '---'}</p>
                                        <p className="text-[10px] text-end-text-sec font-mono">{nota.emitente_cnpj === (nota.empresas?.cnpj) ? nota.destinatario_cnpj : nota.emitente_cnpj}</p>
                                    </td>
                                    <td className="p-4">
                                        <p className="text-sm font-black text-white">{(nota.valor_total || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</p>
                                    </td>
                                    <td className="p-4">
                                        <p className="text-sm text-end-text-sec">
                                            {nota.data_emissao ? new Date(nota.data_emissao).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : '---'}
                                        </p>
                                    </td>
                                    <td className="p-4">
                                        <div className={cn(
                                            "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[9px] font-black uppercase tracking-widest",
                                            nota.status === 'irregular'
                                                ? "bg-end-error/20 text-end-error border border-end-error/20"
                                                : "bg-end-success/20 text-end-success border border-end-success/20"
                                        )}>
                                            {nota.status === 'irregular' ? <AlertCircle size={10} /> : <CheckCircle2 size={10} />}
                                            {nota.status === 'irregular' ? 'Inconsistência' : 'Auditada'}
                                        </div>
                                    </td>
                                    <td className="p-4 text-center">
                                        <button
                                            onClick={() => window.open(`https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx?tipoConsulta=completa&chaveAcesso=${nota.chave_acesso}`, '_blank')}
                                            className="p-2 text-end-text-sec hover:text-end-accent transition-colors"
                                            title="Ver na SEFAZ"
                                        >
                                            <ArrowUpRight size={16} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {total > 20 && (
                    <div className="p-4 border-t border-end-border flex items-center justify-between bg-white/[0.01]">
                        <p className="text-xs text-end-text-sec">Mostrando <span className="text-white font-bold">{notas.length}</span> de <span className="text-white font-bold">{total}</span> documentos</p>
                        <div className="flex gap-2">
                            <button
                                disabled={filters.page === 1}
                                onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
                                className="px-3 py-1 bg-white/5 border border-end-border rounded text-xs font-bold text-white disabled:opacity-20 hover:bg-white/10 transition-all"
                            >
                                Anterior
                            </button>
                            <button
                                disabled={filters.page * 20 >= total}
                                onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
                                className="px-3 py-1 bg-white/5 border border-end-border rounded text-xs font-bold text-white disabled:opacity-20 hover:bg-white/10 transition-all"
                            >
                                Próxima
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
