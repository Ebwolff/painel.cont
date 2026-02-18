import React, { useEffect, useState } from 'react';
import { Building2, Users, TrendingUp, AlertOctagon, FileText } from 'lucide-react';
import { api } from '../../services/api';

interface DashboardStats {
    total_tenants: number;
    active_users: number;
    processed_xmls: number;
    recent_tenants: any[];
}

export function AdminDashboard() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, []);

    async function fetchStats() {
        try {
            const data = await api.get('/admin/dashboard-stats');
            setStats(data);
        } catch (error) {
            console.error("Failed to fetch admin stats", error);
        } finally {
            setLoading(false);
        }
    }

    if (loading) {
        return <div className="text-white p-8">Carregando painel...</div>;
    }

    const cards = [
        { label: 'Total de Escritórios', value: stats?.total_tenants || 0, icon: Building2, color: 'text-blue-500' },
        { label: 'Usuários Ativos', value: stats?.active_users || 0, icon: Users, color: 'text-green-500' },
        { label: 'XMLs Processados', value: stats?.processed_xmls || 0, icon: FileText, color: 'text-end-accent' },
        { label: 'Alertas de Sistema', value: '0', icon: AlertOctagon, color: 'text-red-500' }, // Mocked for now
    ];

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
                    <h3 className="text-lg font-bold text-white mb-6">Atividade Recente do Sistema</h3>
                    <div className="space-y-4">
                        {/* Mock activity for visual balance, since we don't have an activity log table yet */}
                        <div className="flex items-start gap-3 p-4 border-b border-white/5 last:border-0 opacity-50">
                            <div className="w-2 h-2 mt-2 bg-gray-500 rounded-full" />
                            <div>
                                <p className="text-sm text-gray-300">Sistema iniciado</p>
                                <p className="text-xs text-end-text-sec mt-1">Agora</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
