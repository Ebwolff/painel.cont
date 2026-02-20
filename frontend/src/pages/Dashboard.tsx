import React, { useEffect, useState } from 'react';
import { RiskThermometer } from '../components/RiskThermometer';
import { TrendingUp, AlertOctagon, FileText } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { cn } from '../lib/utils';
import { useFeatures } from '../hooks/useFeatures';

interface DashboardMetrics {
    risco_score: number;
    total_notas: number;
    notas_com_erro: number;
    valor_bens_servicos: number;
    credito_tributario_potencial: number;
    status: 'seguro' | 'atencao' | 'critico';
}

interface Alert {
    id: string;
    tipo: string;
    descricao: string;
    created_at: string;
    empresa_razao_social?: string;
}

export function Dashboard() {
    const navigate = useNavigate();
    const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
    const [roiData, setRoiData] = useState<any>(null);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [anomalies, setAnomalies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const { hasFeature, tier } = useFeatures();
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Fetch metrics from our FastAPI backend
        async function fetchMetrics() {
            try {
                console.log("Fetching dashboard metrics...");
                const [metricsData, roiData, alertsData, anomalyData] = await Promise.all([
                    api.get('/dashboard/current-company'),
                    api.get('/roi/summary'),
                    api.get('/alerts'),
                    hasFeature('ai_anomaly_detection') ? api.get('/anomalies/detect') : Promise.resolve({ anomalies: [] })
                ]);

                console.log("Metrics received:", metricsData);
                console.log("ROI received:", roiData);
                console.log("Alerts received:", alertsData);

                setMetrics(metricsData);
                setRoiData(roiData);
                setAlerts(alertsData.slice(0, 5));
                setAnomalies(anomalyData.anomalies || []);
            } catch (error: any) {
                console.error("Failed to fetch dashboard data", error);
                setError(error.message || "Erro desconhecido");
            } finally {
                setLoading(false);
            }
        }
        fetchMetrics();
    }, []);

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
                    <div className="bg-end-error/10 border border-end-error/20 rounded-lg p-4 flex items-center justify-between gap-4 animate-bounce-subtle">
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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                        <span className="text-end-text-sec text-sm font-medium">Total Processado (Mês)</span>
                        <FileText className="text-blue-500" size={20} />
                    </div>
                    <div className="text-2xl font-bold text-white">
                        {stats.total_notas}
                    </div>
                    <div className="text-xs text-end-text-sec mt-1">Processadas no último mês</div>
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
                                        <div className="text-sm font-medium text-white">{alert.descricao}</div>
                                        <div className="text-xs text-end-text-sec">
                                            {alert.empresa_razao_social || 'Escritório'} • {new Date(alert.created_at).toLocaleDateString('pt-BR')}
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
        </div>
    );
}
