import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { FileText, Download, TrendingUp, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function ClientDashboard() {
    const { user, signOut } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState({ total_xml: 0, uploads_month: 0 });
    const [recentFiles, setRecentFiles] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch client data
        // For MVP, we mock or fetch from a new endpoint '/client/stats'
        setLoading(false);
    }, []);

    const handleLogout = async () => {
        await signOut();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-end-bg text-white font-sans">
            {/* Simple Header */}
            <header className="border-b border-white/10 bg-black/20 backdrop-blur-md">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-end-accent to-orange-600 flex items-center justify-center font-black text-black">
                            E
                        </div>
                        <span className="font-bold text-lg tracking-tight">Monitor END</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-bold text-white">{user?.user_metadata?.full_name || 'Cliente'}</p>
                            <p className="text-xs text-end-text-sec">Cliente</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="p-2 hover:bg-white/10 rounded-lg text-end-text-sec hover:text-white transition-colors"
                            title="Sair"
                        >
                            <LogOut size={20} />
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Welcome Section */}
                <div className="mb-8">
                    <h1 className="text-3xl font-black text-white mb-2">Painel do Cliente</h1>
                    <p className="text-end-text-sec">Visão geral dos documentos da sua empresa.</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-end-card border border-end-border p-6 rounded-xl relative overflow-hidden group hover:border-end-accent/30 transition-colors">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <FileText size={60} />
                        </div>
                        <p className="text-end-text-sec text-sm font-medium uppercase mb-1">Total de XMLs</p>
                        <h3 className="text-3xl font-black text-white">1,245</h3>
                        <p className="text-xs text-green-400 mt-2 flex items-center gap-1">
                            <TrendingUp size={12} /> +12% esse mês
                        </p>
                    </div>

                    <div className="bg-end-card border border-end-border p-6 rounded-xl relative overflow-hidden group hover:border-end-accent/30 transition-colors">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <Download size={60} />
                        </div>
                        <p className="text-end-text-sec text-sm font-medium uppercase mb-1">Downloads Realizados</p>
                        <h3 className="text-3xl font-black text-white">850</h3>
                        <p className="text-xs text-end-text-sec mt-2">Último download hoje</p>
                    </div>
                    {/* Placeholder for more stats */}
                    <div className="bg-end-card border border-end-border p-6 rounded-xl relative overflow-hidden flex items-center justify-center text-end-text-sec border-dashed">
                        <p className="text-sm">Mais métricas em breve</p>
                    </div>
                </div>


                {/* Recent Files Section */}
                <div className="bg-end-card border border-end-border rounded-xl overflow-hidden">
                    <div className="p-6 border-b border-white/5 flex items-center justify-between">
                        <h3 className="text-lg font-bold text-white">Arquivos Recentes</h3>
                        <button className="text-xs font-bold text-end-accent hover:text-white transition-colors uppercase">Ver Todos</button>
                    </div>
                    <div className="divide-y divide-white/5">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <div key={i} className="p-4 hover:bg-white/5 transition-colors flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
                                        <FileText size={20} />
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-white">NFe-352309...</p>
                                        <p className="text-xs text-end-text-sec">Recebido em 16/02/2026</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="text-xs bg-green-500/10 text-green-400 px-2 py-1 rounded font-bold uppercase">Autorizada</span>
                                    <button className="p-2 hover:bg-white/10 rounded-lg text-end-text-sec hover:text-white transition-colors">
                                        <Download size={18} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
}
