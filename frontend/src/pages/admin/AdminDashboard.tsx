import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Users, TrendingUp, AlertOctagon, FileText, RefreshCcw } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../lib/utils';

interface DashboardStats {
    total_tenants: number;
    active_users: number;
    processed_xmls: number;
    recent_tenants: any[];
    plan_stats?: {
        counts: { starter: number; pro: number; enterprise: number };
        mrr: number;
    };
}

export function AdminDashboard() {
    const navigate = useNavigate();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [requests, setRequests] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, []);

    async function fetchStats() {
        try {
            const [statsData, requestsData] = await Promise.all([
                api.get('/admin/dashboard-stats'),
                api.get('/admin/requests?status=pending')
            ]);
            setStats(statsData);
            setRequests(requestsData);
        } catch (error) {
            console.error("Failed to fetch admin data", error);
        } finally {
            setLoading(false);
        }
    }

    const handleProcessRequest = async (id: string, status: 'approved' | 'rejected') => {
        try {
            await api.put(`/admin/requests/${id}/process`, { status });
            // Atualizar lista local
            setRequests(prev => prev.filter(r => r.id !== id));
            // Recarregar stats para atualizar distribuição de planos
            fetchStats();
        } catch (error) {
            console.error("Failed to process request", error);
        }
    };

    if (loading) {
        return <div className="text-white p-8">Carregando painel...</div>;
    }

    const cards = [
        { label: 'Total de Escritórios', value: stats?.total_tenants || 0, icon: Building2, color: 'text-blue-500' },
        { label: 'Usuários Ativos', value: stats?.active_users || 0, icon: Users, color: 'text-green-500' },
        { label: 'XMLs Processados', value: stats?.processed_xmls || 0, icon: FileText, color: 'text-end-accent' },
        { label: 'Alertas de Sistema', value: '0', icon: AlertOctagon, color: 'text-red-500' }, // Mocked for now
    ];

    const distributionData = [
        { label: 'Monitor Inicial', key: 'starter', count: stats?.plan_stats?.counts.starter || 0, color: 'bg-gray-500' },
        { label: 'Monitor Profissional', key: 'pro', count: stats?.plan_stats?.counts.pro || 0, color: 'bg-blue-500' },
        { label: 'Inteligência Corporativa', key: 'enterprise', count: stats?.plan_stats?.counts.enterprise || 0, color: 'bg-end-accent' }
    ];

    const totalStats = stats?.total_tenants || 1; // avoid division by zero

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div>
                <h1 className="text-3xl font-black text-white tracking-tight mb-2">Visão Geral</h1>
                <p className="text-end-text-sec">Monitoramento em tempo real da plataforma SaaS.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards.map((stat, index) => (
                    <div key={index} className="bg-end-card border border-end-border rounded-xl p-6 hover:border-white/20 transition-colors">
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-white/5 rounded-lg">
                                <stat.icon size={24} className={stat.color} />
                            </div>
                            {/* <span className="text-xs font-bold bg-white/5 px-2 py-1 rounded text-end-text-sec">+0% mês</span> */}
                        </div>
                        <p className="text-end-text-sec text-xs uppercase font-bold tracking-wider">{stat.label}</p>
                        <h3 className="text-3xl font-black text-white mt-1">{stat.value}</h3>
                    </div>
                ))}
            </div>

            {requests.length > 0 && (
                <div className="bg-end-card border-2 border-end-accent/30 rounded-xl p-6 shadow-[0_0_30px_rgba(235,255,2,0.05)] animate-in zoom-in-95 duration-500">
                    <div className="flex items-center gap-2 mb-6">
                        <div className="w-2 h-2 bg-end-accent rounded-full animate-pulse" />
                        <h3 className="text-lg font-bold text-white uppercase tracking-tighter italic">Solicitações de Upgrade Pendentes ({requests.length})</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {requests.map((req) => (
                            <div key={req.id} className="bg-white/5 border border-white/10 rounded-lg p-5 flex flex-col justify-between gap-4 group hover:border-end-accent/30 transition-all">
                                <div>
                                    <div className="flex justify-between items-start mb-2">
                                        <p className="text-sm font-black text-white uppercase">{req.tenants?.nome}</p>
                                        <span className="text-[10px] bg-end-accent text-black font-black px-2 py-0.5 rounded">UPGRADE</span>
                                    </div>
                                    <p className="text-xs text-end-text-sec mb-4">Solicitou plano: <span className="text-white font-bold">{req.requested_plan === 'enterprise' ? 'Inteligência Corporativa' : 'Monitor Profissional'}</span></p>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => handleProcessRequest(req.id, 'approved')}
                                        className="flex-1 bg-end-accent text-black text-xs font-black py-2 rounded uppercase hover:scale-[1.02] active:scale-95 transition-all"
                                    >
                                        Aprovar
                                    </button>
                                    <button
                                        onClick={() => handleProcessRequest(req.id, 'rejected')}
                                        className="flex-1 bg-white/5 text-center text-white text-xs font-bold py-2 rounded uppercase hover:bg-white/10 transition-all"
                                    >
                                        Recusar
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-end-card border border-end-border rounded-xl p-6">
                    <h3 className="text-lg font-bold text-white mb-6">Últimos Escritórios Cadastrados</h3>
                    <div className="space-y-4">
                        {stats?.recent_tenants?.map((tenant) => (
                            <div key={tenant.id} className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center text-blue-500 font-bold">
                                        <Building2 size={18} />
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-white">{tenant.nome}</p>
                                        <p className="text-xs text-end-text-sec">{tenant.plano} • {new Date(tenant.created_at).toLocaleDateString()}</p>
                                    </div>
                                </div>
                                <span className="text-xs text-green-500 bg-green-500/10 px-2 py-1 rounded">Ativo</span>
                            </div>
                        ))}
                        {(!stats?.recent_tenants || stats.recent_tenants.length === 0) && (
                            <p className="text-end-text-sec text-sm">Nenhum escritório recente.</p>
                        )}
                    </div>
                </div>

                <div className="bg-end-card border border-end-border rounded-xl p-6">
                    <h3 className="text-lg font-bold text-white mb-6">Distribuição de Planos (SaaS)</h3>
                    <div className="space-y-6">
                        {distributionData.map(item => {
                            const percent = Math.round((item.count / totalStats) * 100);
                            return (
                                <div key={item.label}>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-xs font-bold text-white uppercase">{item.label}</span>
                                        <span className="text-xs text-end-text-sec">{item.count} escritórios ({percent}%)</span>
                                    </div>
                                    <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                                        <div
                                            className={cn("h-full rounded-full transition-all duration-1000", item.color)}
                                            style={{ width: `${percent}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}

                        <div className="mt-8 pt-6 border-t border-white/5">
                            <div className="flex justify-between items-center">
                                <div>
                                    <p className="text-xs text-end-text-sec uppercase font-bold">MRR Estimado</p>
                                    <p className="text-2xl font-black text-white tracking-tighter">
                                        {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(stats?.plan_stats?.mrr || 0)}
                                    </p>
                                </div>
                                <TrendingUp className="text-green-500" size={32} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="bg-end-accent/5 border border-end-accent/20 rounded-xl p-8 flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-6">
                    <div className="w-16 h-16 bg-end-accent/20 rounded-2xl flex items-center justify-center text-end-accent shadow-[0_0_20px_rgba(235,255,2,0.1)]">
                        <RefreshCcw size={32} />
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Inteligência Fiscal 2.0</h3>
                        <p className="text-sm text-end-text-sec">O motor de cruzamento está operando com alíquotas federais atualizadas.</p>
                        <div className="flex items-center gap-4 mt-2">
                            <span className="text-[10px] font-bold text-end-success flex items-center gap-1 uppercase">
                                <div className="w-1.5 h-1.5 bg-end-success rounded-full animate-pulse" />
                                Sistema Saudável
                            </span>
                            <span className="text-[10px] font-bold text-end-text-sec uppercase">
                                Última Sincronização: Hoje, {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </div>
                    </div>
                </div>
                <button
                    onClick={() => navigate('/admin/rules')}
                    className="bg-white/10 hover:bg-white/20 text-white px-6 py-2.5 rounded-lg font-bold text-sm transition-all border border-white/10"
                >
                    Gerenciar Regras
                </button>
            </div>
        </div>
    );
}
