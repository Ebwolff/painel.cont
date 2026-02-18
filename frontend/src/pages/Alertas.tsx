import React, { useEffect, useState } from 'react';
import { AlertCircle, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../lib/utils';

export function Alertas() {
    const [alerts, setAlerts] = useState<any[]>([]);
    const [companies, setCompanies] = useState<any[]>([]);
    const [summary, setSummary] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        empresa_id: '',
        status: 'pendente' // Padrão
    });
    const [selectedAlert, setSelectedAlert] = useState<any>(null);

    const fetchData = React.useCallback(async () => {
        setLoading(true);
        try {
            const queryParams = new URLSearchParams();
            if (filters.empresa_id) queryParams.append('empresa_id', filters.empresa_id);
            if (filters.status) queryParams.append('status', filters.status);

            const [alertsData, summaryData, companiesData] = await Promise.all([
                api.get(`/alerts/?${queryParams.toString()}`),
                api.get('/alerts/summary'),
                api.get('/companies/')
            ]);

            setAlerts(alertsData);
            setSummary(summaryData);
            setCompanies(companiesData);
        } catch (error) {
            console.error("Failed to fetch alerts data", error);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const groupedAlerts = React.useMemo(() => {
        const groups: Record<string, any> = {};
        alerts.forEach(alerta => {
            const key = alerta.nota_fiscal_id || alerta.id;

            if (!groups[key]) {
                groups[key] = {
                    ...alerta,
                    ids: [alerta.id],
                    items: [alerta],
                    totalDiferenca: alerta.diferenca || 0,
                    totalEsperado: alerta.valor_esperado || 0,
                    totalEncontrado: alerta.valor_encontrado || 0,
                    tipos: [alerta.tipo]
                };
            } else {
                groups[key].ids.push(alerta.id);
                groups[key].items.push(alerta);
                groups[key].totalDiferenca += (alerta.diferenca || 0);
                groups[key].totalEsperado += (alerta.valor_esperado || 0);
                groups[key].totalEncontrado += (alerta.valor_encontrado || 0);
                if (!groups[key].tipos.includes(alerta.tipo)) {
                    groups[key].tipos.push(alerta.tipo);
                }
                const severityOrder: any = { 'critica': 3, 'alta': 2, 'media': 1, 'baixa': 0 };
                if (severityOrder[alerta.severidade] > severityOrder[groups[key].severidade]) {
                    groups[key].severidade = alerta.severidade;
                }
            }
        });
        return Object.values(groups).map((g: any) => {
            if (g.tipos.length > 1) {
                const tributos = g.tipos.map((t: string) => t.split('_')[0].toUpperCase()).sort().join(' e ');
                g.mensagem_resumida = `Inconsistência em ${tributos}`;
            } else {
                g.mensagem_resumida = g.mensagem;
            }
            return g;
        });
    }, [alerts]);

    const handleResolve = async (group: any) => {
        if (!confirm(`Deseja marcar os alertas da nota ${group.notas_fiscais?.numero || 'S/N'} como resolvidos?`)) return;
        try {
            await Promise.all(group.ids.map((id: string) => api.post(`/alerts/${id}/resolver`, {})));

            setSelectedAlert(null);
            fetchData(); // Recarregar
        } catch (error) {
            alert("Erro ao resolver alertas.");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white">Alertas de Conformidade</h2>
                    <p className="text-sm text-end-text-sec">Gestão proativa de inconsistências fiscais.</p>
                </div>

                <div className="flex items-center gap-3">
                    <select
                        value={filters.empresa_id}
                        onChange={e => setFilters({ ...filters, empresa_id: e.target.value })}
                        className="bg-end-card border border-end-border text-end-text-sec text-xs font-bold py-2 px-3 rounded focus:outline-none focus:border-end-accent transition-colors"
                    >
                        <option value="">Todas as Empresas</option>
                        {companies.map(c => (
                            <option key={c.id} value={c.id}>{c.razao_social}</option>
                        ))}
                    </select>

                    <select
                        value={filters.status}
                        onChange={e => setFilters({ ...filters, status: e.target.value })}
                        className="bg-end-card border border-end-border text-end-text-sec text-xs font-bold py-2 px-3 rounded focus:outline-none focus:border-end-accent transition-colors"
                    >
                        <option value="pendente">Pendentes</option>
                        <option value="resolvido">Resolvidos</option>
                    </select>
                </div>
            </div>

            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-end-card border border-end-border p-4 rounded-lg">
                        <div className="text-[10px] font-bold text-end-error uppercase mb-1">Críticos</div>
                        <div className="text-2xl font-bold text-white">{summary.counts.critica || 0}</div>
                    </div>
                    <div className="bg-end-card border border-end-border p-4 rounded-lg">
                        <div className="text-[10px] font-bold text-end-warning uppercase mb-1">Atenção</div>
                        <div className="text-2xl font-bold text-white">{(summary.counts.alta || 0) + (summary.counts.media || 0)}</div>
                    </div>
                    <div className="bg-end-card border border-end-border p-4 rounded-lg">
                        <div className="text-[10px] font-bold text-end-success uppercase mb-1">Resolvidos</div>
                        <div className="text-2xl font-bold text-white">{summary.total_pendentes === 0 ? 'Meta ok' : 'Em curso'}</div>
                    </div>
                    <div className="bg-end-card border border-end-border p-4 rounded-lg">
                        <div className="text-[10px] font-bold text-end-accent uppercase mb-1">Total Pendente</div>
                        <div className="text-2xl font-bold text-white">{summary.total_pendentes}</div>
                    </div>
                </div>
            )}

            <div className="bg-end-card border border-end-border rounded-lg overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-white/5 border-b border-end-border">
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Status</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Mensagem</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Nota</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Empresa</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Data</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan={6} className="p-8 text-center text-end-text-sec animate-pulse">Carregando alertas...</td></tr>
                        ) : groupedAlerts.length === 0 ? (
                            <tr><td colSpan={6} className="p-8 text-center text-end-text-sec">Nenhum alerta encontrado.</td></tr>
                        ) : groupedAlerts.map((alerta: any) => (
                            <tr key={alerta.id} className="border-b border-end-border last:border-0 hover:bg-white/5 transition-colors">
                                <td className="p-4">
                                    {alerta.severidade === 'critica' && <AlertOctagon size={20} className="text-end-error" />}
                                    {alerta.severidade === 'alta' && <AlertCircle size={20} className="text-end-warning" />}
                                    {alerta.severidade === 'media' && <AlertCircle size={20} className="text-yellow-200" />}
                                    {alerta.severidade === 'baixa' && <CheckCircle2 size={20} className="text-end-success" />}
                                </td>
                                <td className="p-4 text-sm text-white font-medium">{alerta.mensagem_resumida}</td>
                                <td className="p-4 text-sm text-end-text-sec font-mono">
                                    {alerta.notas_fiscais?.numero || 'S/N'}
                                </td>
                                <td className="p-4 text-sm text-end-text-sec">
                                    {alerta.notas_fiscais?.empresas?.razao_social || alerta.empresas?.razao_social || alerta.notas_fiscais?.destinatario_nome || 'Desconhecida'}
                                </td>
                                <td className="p-4 text-sm text-end-text-sec">
                                    {new Date(alerta.created_at).toLocaleDateString('pt-BR')}
                                </td>
                                <td className="p-4">
                                    <button
                                        onClick={() => setSelectedAlert(alerta)}
                                        className="text-xs text-end-accent hover:underline"
                                    >
                                        Ver detalhes
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>


            {/* Modal de Detalhes */}
            {
                selectedAlert && (
                    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                        <div className="bg-end-card border border-end-border rounded-lg max-w-lg w-full p-6 shadow-2xl relative">
                            <button
                                onClick={() => setSelectedAlert(null)}
                                className="absolute top-4 right-4 text-end-text-sec hover:text-white"
                            >
                                ✕
                            </button>

                            <div className="flex items-center gap-3 mb-6">
                                {selectedAlert.severidade === 'critica' && <AlertOctagon size={24} className="text-end-error" />}
                                {selectedAlert.severidade === 'alta' && <AlertCircle size={24} className="text-end-warning" />}
                                {selectedAlert.severidade === 'media' && <AlertCircle size={24} className="text-yellow-200" />}
                                {selectedAlert.severidade === 'baixa' && <CheckCircle2 size={24} className="text-end-success" />}
                                <h3 className="text-xl font-bold text-white">Detalhamento da Nota {selectedAlert.notas_fiscais?.numero || 'S/N'}</h3>
                            </div>

                            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
                                {selectedAlert.items.map((item: any, idx: number) => (
                                    <div key={item.id} className={cn("p-4 rounded-lg bg-white/5 border border-white/10", idx > 0 && "mt-4")}>
                                        <div className="flex justify-between items-start mb-2">
                                            <span className="text-[10px] font-bold text-end-accent uppercase">{item.tipo.replace('_', ' ')}</span>
                                            <span className="text-[10px] font-bold text-end-text-sec">{new Date(item.created_at).toLocaleDateString('pt-BR')}</span>
                                        </div>
                                        <p className="text-sm text-white mb-3">{item.mensagem}</p>

                                        <div className="grid grid-cols-2 gap-4 text-[10px] uppercase font-bold text-end-text-sec">
                                            <div>
                                                <span>Esperado</span>
                                                <p className="text-white text-xs">R$ {(item.valor_esperado || 0).toFixed(2)}</p>
                                            </div>
                                            <div>
                                                <span>Encontrado</span>
                                                <p className="text-white text-xs">R$ {(item.valor_encontrado || 0).toFixed(2)}</p>
                                            </div>
                                        </div>
                                        <div className="mt-2 pt-2 border-t border-white/5">
                                            <span className="text-[10px] uppercase font-bold text-end-error">Diferença</span>
                                            <p className="text-end-error text-sm font-bold">R$ {(item.diferenca || 0).toFixed(2)}</p>
                                        </div>
                                    </div>
                                ))}

                                <div className="p-4 rounded-lg bg-end-accent/10 border border-end-accent/20 mt-6">
                                    <div className="flex justify-between items-center">
                                        <span className="text-xs font-bold text-white uppercase">Impacto Total da Nota</span>
                                        <span className="text-lg font-black text-end-accent">R$ {(selectedAlert.totalDiferenca || 0).toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-8 flex justify-end gap-3">
                                <button className="px-4 py-2 text-sm text-end-text-sec hover:text-white" onClick={() => setSelectedAlert(null)}>
                                    Fechar
                                </button>
                                {!selectedAlert.resolvido && (
                                    <button
                                        onClick={() => handleResolve(selectedAlert)}
                                        className="px-4 py-2 bg-end-accent text-black font-bold text-sm rounded hover:bg-end-accent/90"
                                    >
                                        Resolver Todas as Pendências
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    );
}
