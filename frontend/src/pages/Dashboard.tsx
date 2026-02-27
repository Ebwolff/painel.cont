import React, { useEffect, useState } from 'react';
import { RiskThermometer } from '../components/RiskThermometer';
import { TrendingUp, AlertOctagon, FileText, ShieldCheck, X, Activity } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { cn } from '../lib/utils';
import { useFeatures } from '../hooks/useFeatures';

interface DashboardMetrics {
    risco_score: number;
    total_notas: number;
    notas_emitidas: number;
    notas_recebidas: number;
    notas_com_erro: number;
    valor_bens_servicos: number;
    credito_tributario_potencial: number;
    status: 'seguro' | 'atencao' | 'critico';
}

interface Alert {
    id: string;
    tipo: string;
    mensagem?: string;
    descricao?: string;
    created_at: string;
    empresa_razao_social?: string;
}

export function Dashboard() {
    const navigate = useNavigate();
    const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
    const [roiData, setRoiData] = useState<any>(null);
    const [assistedData, setAssistedData] = useState<any>(null);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [anomalies, setAnomalies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const { hasFeature, tier } = useFeatures();
    const [error, setError] = useState<string | null>(null);
    const [isAnomalyModalOpen, setIsAnomalyModalOpen] = useState(false);

    useEffect(() => {
        // Fetch metrics from our FastAPI backend
        async function fetchMetrics() {
            try {
                console.log("Fetching dashboard metrics...");
                const [metricsData, roiDataRes, alertsDataRes, anomalyDataRes, assistedRes] = await Promise.all([
                    api.get('/dashboard/current-company').catch(e => ({ error: true, message: e.message })),
                    api.get('/roi/summary').catch(e => ({ error: true })),
                    api.get('/alerts').catch(e => []),
                    hasFeature('ai_anomaly_detection') ? api.get('/anomalies/detect').catch(e => ({ anomalies: [] })) : Promise.resolve({ anomalies: [] }),
                    api.get('/simulation/assisted-calculation').catch(e => null)
                ]);

                console.log("Metrics received:", metricsData);

                // Defensive check for metrics
                if (metricsData && !metricsData.error) {
                    setMetrics(metricsData);
                }

                if (assistedRes) {
                    setAssistedData(assistedRes);
                }

                // Defensive check for ROI
                if (roiDataRes && !roiDataRes.error) {
                    setRoiData(roiDataRes);
                }

                // Defensive check for Alerts - Support both array directly or {data: []}
                const rawAlerts = Array.isArray(alertsDataRes) ? alertsDataRes : (alertsDataRes?.data || []);
                setAlerts(rawAlerts.slice(0, 5));

                // Defensive check for Anomalies
                setAnomalies(Array.isArray(anomalyDataRes?.anomalies) ? anomalyDataRes.anomalies : []);
            } catch (error: any) {
                console.error("Critical failure in dashboard data fetch", error);
                setError(error.message || "Erro ao carregar dados do painel");
            } finally {
                setLoading(false);
            }
        }
        fetchMetrics();
    }, [hasFeature]);

    if (loading) {
        return (
            <div className="space-y-8 animate-pulse">
                <div className="flex justify-between items-end">
                    <div className="space-y-3">
                        <div className="h-8 w-64 bg-white/5 rounded"></div>
                        <div className="h-4 w-96 bg-white/5 rounded"></div>
                    </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-32 bg-end-card border border-end-border rounded-lg"></div>
                    ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="h-[300px] bg-end-card border border-end-border rounded-lg"></div>
                    <div className="h-[300px] bg-end-card border border-end-border rounded-lg"></div>
                </div>
            </div>
        );
    }

    // Default values if data is missing
    const stats = {
        risco_score: metrics?.risco_score ?? 0,
        total_notas: metrics?.total_notas ?? 0,
        notas_emitidas: metrics?.notas_emitidas ?? 0,
        notas_recebidas: metrics?.notas_recebidas ?? 0,
        notas_com_erro: metrics?.notas_com_erro ?? 0,
        valor_bens_servicos: metrics?.valor_bens_servicos ?? 0,
        credito_tributario_potencial: metrics?.credito_tributario_potencial ?? 0,
        status: metrics?.status ?? 'seguro'
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Painel de Controle</h2>
                    <p className="text-end-text-sec">Bem-vindo ao END Monitor. Aqui está o resumo da conformidade tributária.</p>
                </div>

                {/* ROI / Value Realization Card */}
                {roiData && (
                    <div className="bg-end-accent/10 border border-end-accent/20 rounded-lg p-4 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 bg-end-accent rounded-full flex items-center justify-center text-black">
                                <TrendingUp size={24} />
                            </div>
                            <div>
                                <p className="text-[10px] uppercase font-bold text-end-accent tracking-wider">Valor Gerado p/ Cliente</p>
                                <p className="text-xl font-black text-white">R$ {(roiData?.total_creditos_identificados || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                                <p className="text-[11px] text-end-text-sec italic">Calculado em créditos CBS/IBS identificados</p>
                            </div>
                        </div>
                        <span className="bg-end-accent/20 text-end-accent text-[9px] px-2 py-0.5 rounded font-black border border-end-accent/30 lowercase">pro</span>
                    </div>
                )}

                {hasFeature('ai_anomaly_detection') && anomalies.length > 0 && (
                    <div
                        onClick={() => setIsAnomalyModalOpen(true)}
                        className="bg-end-error/10 border border-end-error/20 rounded-lg p-4 flex items-center justify-between gap-4 animate-bounce-subtle cursor-pointer hover:bg-end-error/20 transition-colors shadow-lg shadow-end-error/5"
                    >
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 bg-end-error rounded-full flex items-center justify-center text-white">
                                <AlertOctagon size={24} />
                            </div>
                            <div>
                                <p className="text-[10px] uppercase font-bold text-end-error tracking-wider italic">Alerta de Anomalia (IA)</p>
                                <p className="text-xl font-black text-white">{anomalies.length} Comportamentos Atípicos</p>
                                <p className="text-[11px] text-end-text-sec">Detectado desvio de faturamento acima da média</p>
                            </div>
                        </div>
                        <span className="bg-end-error/20 text-end-error text-[9px] px-2 py-0.5 rounded font-black border border-end-error/30 lowercase italic">enterprise</span>
                    </div>
                )}

                {/* Assisted Calculation Preview */}
                {assistedData && (
                    <div className="bg-white/5 border border-white/10 rounded-lg p-4 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                                <ShieldCheck size={24} />
                            </div>
                            <div>
                                <p className="text-[10px] uppercase font-bold text-end-text-sec tracking-wider">Apuração Assistida (Pré-Guia)</p>
                                <p className="text-xl font-black text-white">
                                    {(assistedData.consolidado.total_tributos || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                </p>
                                <p className="text-[11px] text-end-text-sec italic">Baseado em notas validadas este mês</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-[10px] text-end-text-sec uppercase mb-1">Alíquota Efetiva</p>
                            <p className="text-sm font-bold text-end-accent">{assistedData.aliquota_efetiva}%</p>
                        </div>
                    </div>
                )}
            </div>

            {tier === 'starter' && (
                <div className="bg-gradient-to-r from-end-accent/10 to-transparent border-l-4 border-end-accent p-6 rounded-r-lg">
                    <h4 className="text-lg font-bold text-white mb-1">Evolua para o Plano PRO</h4>
                    <p className="text-sm text-end-text-sec mb-4">Desbloqueie o Monitor de Sincronização Automática via SEFAZ e as Calculadoras de ROI.</p>
                    <button
                        onClick={() => navigate('/planos')}
                        className="bg-end-accent text-black px-6 py-2 rounded font-black text-xs hover:scale-105 transition-transform"
                    >
                        CONHECER PLANOS
                    </button>
                </div>
            )}

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-end-card border border-end-border p-5 rounded-lg border-l-4 border-l-blue-500 shadow-lg shadow-blue-500/5">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-end-text-sec text-sm font-medium uppercase tracking-wider">Recuperação Tributária</span>
                        <TrendingUp className="text-blue-500" size={20} />
                    </div>
                    <div className="text-2xl font-black text-white">
                        R$ {stats.credito_tributario_potencial.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </div>
                    <div className="text-[10px] text-blue-400 mt-1 font-bold uppercase">Auditoria Monofásica Ativa</div>
                </div>

                <div className="bg-end-card border border-end-border p-5 rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-end-text-sec text-sm font-medium">Notas com Divergência</span>
                        <AlertOctagon className="text-end-error" size={20} />
                    </div>
                    <div className="text-2xl font-bold text-white">
                        {stats.notas_com_erro}
                    </div>
                    <div className="text-xs text-end-text-sec mt-1 text-end-error font-medium">Ação necessária imediata</div>
                </div>

                <div className="bg-end-card border border-end-border p-5 rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-end-text-sec text-sm font-medium">Notas Emitidas</span>
                        <FileText className="text-blue-500" size={20} />
                    </div>
                    <div className="text-2xl font-bold text-white">
                        {stats.notas_emitidas}
                    </div>
                    <div className="text-xs text-end-text-sec mt-1">Saídas processadas (Mês)</div>
                </div>

                <div className="bg-end-card border border-end-border p-5 rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-end-text-sec text-sm font-medium">Notas Recebidas</span>
                        <FileText className="text-purple-500" size={20} />
                    </div>
                    <div className="text-2xl font-bold text-white">
                        {stats.notas_recebidas}
                    </div>
                    <div className="text-xs text-end-text-sec mt-1">Entradas processadas (Mês)</div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className={cn(
                    "bg-end-card border rounded-lg flex flex-col items-center justify-center min-h-[300px] transition-all",
                    stats.status === 'critico' ? "border-end-error/30 shadow-[0_0_20px_rgba(239,68,68,0.1)]" :
                        stats.status === 'atencao' ? "border-end-warning/30 shadow-[0_0_20px_rgba(245,158,11,0.1)]" :
                            "border-end-border"
                )}>
                    <h3 className="text-lg font-semibold text-white mb-6 w-full text-center">Índice de Exposição Fiscal</h3>
                    <RiskThermometer score={stats.risco_score} size={280} />
                    <p className="text-sm text-end-text-sec mt-6 text-center max-w-sm">
                        Calculado com base na auditoria de 100% dos XMLs via motor de regras inteligente.
                    </p>
                </div>

                <div className="bg-end-card border border-end-border p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-white mb-4">Últimas Ocorrências</h3>
                    <div className="space-y-3">
                        {alerts.length === 0 ? (
                            <p className="text-xs text-end-text-sec text-center py-4 italic">Nenhuma inconformidade detectada.</p>
                        ) : (
                            alerts.map((alert) => (
                                <div key={alert.id} className="flex items-start gap-3 p-3 bg-white/5 rounded border border-white/5 hover:border-end-border transition-colors cursor-pointer">
                                    <AlertOctagon size={16} className={cn(
                                        "mt-1 shrink-0",
                                        alert.tipo === 'fiscal' ? "text-end-error" : "text-end-warning"
                                    )} />
                                    <div>
                                        <div className="text-sm font-medium text-white">{alert.descricao || alert.mensagem || 'Alerta de Conformidade'}</div>
                                        <div className="text-xs text-end-text-sec">
                                            {alert.empresa_razao_social || 'Escritório'} • {alert.created_at ? new Date(alert.created_at).toLocaleDateString('pt-BR') : 'Data Indisponível'}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                        {alerts.length > 0 && (
                            <div className="pt-2 text-center">
                                <Link to="/alertas" className="text-xs text-end-accent hover:underline">Ver todos os alertas →</Link>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Anomaly Modal */}
            {isAnomalyModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-end-card border border-end-border rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[80vh]">
                        <div className="p-4 border-b border-end-border flex justify-between items-center bg-end-error/10">
                            <h3 className="font-bold text-white flex items-center gap-2">
                                <Activity size={18} className="text-end-error" />
                                Relatório de Anomalias (IA)
                            </h3>
                            <button onClick={() => setIsAnomalyModalOpen(false)} className="text-end-text-sec hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-4">
                            <p className="text-sm text-end-text-sec mb-4">
                                {anomalies.length} comportamento(s) atípico(s) detectado(s) pelo nosso motor de IA nos últimos 30 dias.
                            </p>
                            <div className="space-y-3">
                                {anomalies.map((anom, idx) => (
                                    <div key={idx} className="bg-white/5 border border-white/10 p-4 rounded-lg flex gap-4 items-start">
                                        <div className="bg-end-error/20 p-2 rounded-full shrink-0">
                                            <AlertOctagon size={18} className="text-end-error" />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <h4 className="text-white font-bold capitalize">{anom.tipo?.replace('_', ' ')}</h4>
                                                <span className={cn(
                                                    "text-[9px] font-black uppercase px-2 py-0.5 rounded",
                                                    anom.severidade === 'alta' ? "bg-end-error/20 text-end-error" :
                                                        anom.severidade === 'media' ? "bg-end-warning/20 text-end-warning" : "bg-white/10 text-white"
                                                )}>
                                                    Risco: {anom.severidade}
                                                </span>
                                            </div>
                                            <p className="text-sm text-end-text-sec">{anom.detalhe}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="p-4 border-t border-end-border bg-white/[0.02] flex justify-end">
                            <button
                                onClick={() => setIsAnomalyModalOpen(false)}
                                className="bg-white/10 hover:bg-white/20 text-white px-6 py-2 rounded-lg font-bold transition-colors text-sm"
                            >
                                Fechar Relatório
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
