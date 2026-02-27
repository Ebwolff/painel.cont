import React, { useEffect, useState } from 'react';
import { AlertCircle, AlertOctagon, CheckCircle2, Sparkles, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../lib/utils';
import { useFeatures } from '../hooks/useFeatures';
import { useNavigate } from 'react-router-dom';

export function Alertas() {
    const navigate = useNavigate();
    const { hasFeature } = useFeatures();
    const [alerts, setAlerts] = useState<any[]>([]);
    const [companies, setCompanies] = useState<any[]>([]);
    const [summary, setSummary] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        empresa_id: '',
        status: 'pendente'
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

            setAlerts(Array.isArray(alertsData) ? alertsData : []);
            setSummary(summaryData);
            setCompanies(Array.isArray(companiesData) ? companiesData : []);
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
        if (!Array.isArray(alerts)) return [];
        const groups: Record<string, any> = {};
        alerts.forEach(alerta => {
            if (!alerta) return;
            const key = alerta.nota_fiscal_id || alerta.id;

            if (!groups[key]) {
                groups[key] = {
                    ...alerta,
                    ids: [alerta.id],
                    items: [alerta],
                    totalDiferenca: alerta.diferenca || 0,
                    totalEsperado: alerta.valor_esperado || 0,
                    totalEncontrado: alerta.valor_encontrado || 0,
                    tipos: [alerta.tipo],
                    isOpportunity: alerta.is_opportunity || false
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
                if (alerta.is_opportunity) {
                    groups[key].isOpportunity = true;
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
            fetchData();
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

            <div className="bg-end-card border border-end-border rounded-lg overflow-visible">
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
                                    {alerta.isOpportunity ? (
                                        <Sparkles size={20} className="text-blue-400 animate-pulse-subtle" />
                                    ) : (
                                        <>
                                            {alerta.severidade === 'critica' && <AlertOctagon size={20} className="text-end-error" />}
                                            {alerta.severidade === 'alta' && <AlertCircle size={20} className="text-end-warning" />}
                                            {alerta.severidade === 'media' && <AlertCircle size={20} className="text-yellow-200" />}
                                            {alerta.severidade === 'baixa' && <CheckCircle2 size={20} className="text-end-success" />}
                                        </>
                                    )}
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

            {selectedAlert && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                    <div className="bg-end-card border border-end-border rounded-lg max-w-lg w-full p-6 shadow-2xl relative overflow-hidden">
                        <button
                            onClick={() => setSelectedAlert(null)}
                            className="absolute top-4 right-4 text-end-text-sec hover:text-white z-10"
                        >
                            ✕
                        </button>

                        <div className="flex items-center gap-3 mb-6">
                            {selectedAlert.severidade === 'critica' && <AlertOctagon size={24} className="text-end-error" />}
                            {selectedAlert.severidade === 'alta' && <AlertCircle size={24} className="text-end-warning" />}
                            {selectedAlert.severidade === 'media' && <AlertCircle size={24} className="text-yellow-200" />}
                            {selectedAlert.severidade === 'baixa' && <CheckCircle2 size={24} className="text-end-success" />}
                            <div>
                                <h3 className="text-xl font-bold text-white">Detalhamento da Nota {selectedAlert.notas_fiscais?.numero || 'S/N'}</h3>
                                <div className="flex items-center gap-1.5 mt-1">
                                    <Sparkles size={12} className="text-end-accent" />
                                    <span className="text-[10px] text-end-accent font-bold uppercase tracking-tighter">Auditoria Inteligente END 4.0</span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
                            <div>
                                <h4 className="text-[10px] uppercase font-black text-end-text-sec tracking-widest mb-3">Ocorrências de Conformidade</h4>
                                <div className="space-y-3">
                                    {selectedAlert.items.map((item: any) => (
                                        <div key={item.id} className={cn(
                                            "p-3 rounded border",
                                            item.is_opportunity ? "bg-blue-500/10 border-blue-500/20 shadow-[0_0_10px_rgba(59,130,246,0.05)]" : "bg-white/5 border-white/10"
                                        )}>
                                            <div className="flex justify-between items-start mb-1">
                                                <div className="flex items-center gap-1.5">
                                                    {item.is_opportunity && <Sparkles size={10} className="text-blue-400" />}
                                                    <span className={cn("text-[10px] font-bold uppercase", item.is_opportunity ? "text-blue-400" : "text-end-accent")}>
                                                        {item.tipo.replace('_', ' ')}
                                                        {item.is_opportunity && " • OPORTUNIDADE"}
                                                    </span>
                                                </div>
                                                <span className="text-[10px] font-bold text-end-text-sec">{new Date(item.created_at).toLocaleDateString('pt-BR')}</span>
                                            </div>
                                            <p className="text-sm text-white">{item.mensagem}</p>
                                            <div className="mt-2 flex gap-4">
                                                <div className="text-[10px]">
                                                    <span className="text-end-text-sec block">Esperado</span>
                                                    <span className="text-white font-bold">R$ {(item.valor_esperado || 0).toFixed(2)}</span>
                                                </div>
                                                <div className="text-[10px]">
                                                    <span className="text-end-text-sec block">Encontrado</span>
                                                    <span className="text-white font-bold">R$ {(item.valor_encontrado || 0).toFixed(2)}</span>
                                                </div>
                                                <div className="text-[10px]">
                                                    <span className={cn("block font-medium uppercase tracking-tighter", item.is_opportunity ? "text-blue-400" : "text-end-error")}>
                                                        {item.is_opportunity ? "Crédito" : "Diferença"}
                                                    </span>
                                                    <span className={cn("font-black", item.is_opportunity ? "text-blue-400" : "text-end-error")}>
                                                        R$ {(item.diferenca || 0).toFixed(2)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="pt-4 border-t border-white/10">
                                <h4 className="text-[10px] uppercase font-black text-end-text-sec tracking-widest mb-3">Conformidade Consolidada</h4>
                                <div className="grid grid-cols-2 lg:grid-cols-5 gap-2">
                                    <div className="bg-black/20 p-2 rounded border border-white/5">
                                        <p className="text-[8px] text-end-text-sec uppercase font-bold">CBS</p>
                                        <p className={cn("text-[9px] font-black", selectedAlert.validation_details?.cbs_ok ? "text-end-success" : "text-end-error")}>
                                            {selectedAlert.validation_details?.cbs_ok ? "● OK" : "● ALERTA"}
                                        </p>
                                    </div>
                                    <div className="bg-black/20 p-2 rounded border border-white/5">
                                        <p className="text-[8px] text-end-text-sec uppercase font-bold">IBS</p>
                                        <p className={cn("text-[9px] font-black", selectedAlert.validation_details?.ibs_ok ? "text-end-success" : "text-end-error")}>
                                            {selectedAlert.validation_details?.ibs_ok ? "● OK" : "● ALERTA"}
                                        </p>
                                    </div>
                                    <div className="bg-black/20 p-2 rounded border border-white/5">
                                        <p className="text-[8px] text-end-text-sec uppercase font-bold">PIS</p>
                                        <p className={cn("text-[9px] font-black", selectedAlert.validation_details?.pis_ok !== false ? "text-end-success" : "text-end-error")}>
                                            {selectedAlert.validation_details?.pis_ok !== false ? "● OK" : "● ALERTA"}
                                        </p>
                                    </div>
                                    <div className="bg-black/20 p-2 rounded border border-white/5">
                                        <p className="text-[8px] text-end-text-sec uppercase font-bold">COFINS</p>
                                        <p className={cn("text-[9px] font-black", selectedAlert.validation_details?.cofins_ok !== false ? "text-end-success" : "text-end-error")}>
                                            {selectedAlert.validation_details?.cofins_ok !== false ? "● OK" : "● ALERTA"}
                                        </p>
                                    </div>
                                    <div className="bg-black/20 p-2 rounded border border-white/5">
                                        <p className="text-[8px] text-end-text-sec uppercase font-bold">ICMS</p>
                                        <p className={cn("text-[9px] font-black", selectedAlert.validation_details?.icms_ok !== false ? "text-end-success" : "text-end-error")}>
                                            {selectedAlert.validation_details?.icms_ok !== false ? "● OK" : "● ALERTA"}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="pt-4 border-t border-white/10 relative">
                                <div className="flex items-center justify-between mb-3">
                                    <h4 className="text-[10px] uppercase font-black text-end-text-sec tracking-widest">Itens da Nota (XML)</h4>
                                    {!hasFeature('advanced_alerts') && (
                                        <span className="flex items-center gap-1 text-[9px] font-bold text-end-accent uppercase bg-end-accent/10 px-2 py-0.5 rounded">
                                            <ShieldCheck size={10} /> Recurso PRO
                                        </span>
                                    )}
                                </div>

                                <div className={cn(
                                    "bg-black/20 rounded-lg border border-white/5 overflow-hidden transition-all",
                                    !hasFeature('advanced_alerts') ? "blur-[2px] pointer-events-none opacity-50" : ""
                                )}>
                                    <table className="w-full text-left text-[11px]">
                                        <thead className="bg-white/5 text-end-text-sec uppercase font-bold">
                                            <tr>
                                                <th className="p-2">#</th>
                                                <th className="p-2">NCM</th>
                                                <th className="p-2">Produto</th>
                                                <th className="p-2">CBS</th>
                                                <th className="p-2">IBS</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-white/5">
                                            <NoteItemsList notaId={selectedAlert.nota_fiscal_id} />
                                        </tbody>
                                    </table>
                                </div>

                                {!hasFeature('advanced_alerts') && (
                                    <div className="absolute inset-0 flex items-center justify-center bg-transparent z-10">
                                        <button
                                            onClick={() => navigate('/planos')}
                                            className="bg-end-accent text-black px-4 py-1.5 rounded font-black text-[10px] hover:scale-105 transition-transform shadow-lg shadow-end-accent/20 flex items-center gap-2"
                                        >
                                            LIBERAR AUDITORIA TÉCNICA
                                        </button>
                                    </div>
                                )}
                            </div>

                            <div className={cn(
                                "p-4 rounded-lg border shadow-lg transition-transform hover:scale-[1.02]",
                                selectedAlert.isOpportunity
                                    ? "bg-blue-500/10 border-blue-500/30 shadow-blue-500/5"
                                    : "bg-end-accent/10 border-end-accent/20 shadow-end-accent/5"
                            )}>
                                <div className="flex justify-between items-center">
                                    <span className="text-xs font-bold text-white uppercase tracking-tight">
                                        {selectedAlert.isOpportunity ? "Economia Identificada" : "Impacto Fiscal Total"}
                                    </span>
                                    <span className={cn(
                                        "text-xl font-black",
                                        selectedAlert.isOpportunity ? "text-blue-400" : "text-end-accent"
                                    )}>
                                        R$ {(selectedAlert.totalDiferenca || 0).toFixed(2)}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 flex justify-end gap-3 pt-4 border-t border-white/10">
                            <button className="px-4 py-2 text-sm text-end-text-sec hover:text-white" onClick={() => setSelectedAlert(null)}>
                                Fechar
                            </button>
                            {!selectedAlert.resolvido && (
                                <button
                                    onClick={() => handleResolve(selectedAlert)}
                                    className="px-4 py-2 bg-end-accent text-black font-bold text-sm rounded hover:scale-105 transition-transform"
                                >
                                    Resolver Pendências
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function NoteItemsList({ notaId }: { notaId: string }) {
    const [items, setItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!notaId) return;
        setLoading(true);
        api.get(`/items/${notaId}`)
            .then(res => setItems(Array.isArray(res) ? res : []))
            .catch(err => {
                console.error("Erro itens:", err);
                setItems([]);
            })
            .finally(() => setLoading(false));
    }, [notaId]);

    if (loading) return <tr><td colSpan={5} className="p-4 text-center text-end-text-sec animate-pulse">Cruzando dados de itens...</td></tr>;
    if (items.length === 0) return <tr><td colSpan={5} className="p-4 text-center text-end-text-sec italic">Nenhum item detalhado encontrado.</td></tr>;

    return (
        <>
            {items.map((it: any) => (
                <tr key={it.id} className="hover:bg-white/5">
                    <td className="p-2 font-mono text-end-text-sec">{it.n_item}</td>
                    <td className="p-2">
                        <div className="font-bold text-white">{it.ncm}</div>
                        <div className="text-[10px] text-end-text-sec">{it.cfop}</div>
                    </td>
                    <td className="p-2 text-white/80 truncate max-w-[150px]">{it.x_prod || '---'}</td>
                    <td className="p-2">
                        {it.cbs_correto ? (
                            <span className="text-end-success">● OK</span>
                        ) : (
                            <span className="text-end-error font-bold">● ERRO</span>
                        )}
                    </td>
                    <td className="p-2">
                        {it.ibs_correto ? (
                            <span className="text-end-success">● OK</span>
                        ) : (
                            <span className="text-end-error font-bold">● ERRO</span>
                        )}
                    </td>
                </tr>
            ))}
        </>
    );
}
