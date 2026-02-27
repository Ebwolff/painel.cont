import React, { useEffect, useState } from 'react';
import { Plus, Search, Building2, MoreHorizontal, Trash2, Edit2, User, TrendingUp } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../lib/utils';

// --- Tier badge styling ---
const TIER_STYLES: Record<string, { bg: string; text: string }> = {
    'Individual': { bg: 'bg-slate-500/20', text: 'text-slate-300' },
    'Starter': { bg: 'bg-green-500/20', text: 'text-green-400' },
    'Escritório': { bg: 'bg-blue-500/20', text: 'text-blue-400' },
    'Enterprise': { bg: 'bg-amber-500/20', text: 'text-amber-400' },
    'Sem CNPJs': { bg: 'bg-white/10', text: 'text-end-text-sec' },
};

export function TenantsList() {
    const [tenants, setTenants] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newTenant, setNewTenant] = useState({ nome: '', cnpj: '', plano: 'free' });
    const [totalMRR, setTotalMRR] = useState(0);

    const formatCNPJ = (value: string) => {
        const digits = value.replace(/\D/g, '').slice(0, 14);
        return digits
            .replace(/^(\d{2})(\d)/, '$1.$2')
            .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
            .replace(/(\d{3})(\d)/, '.$1/$2')
            .replace(/(\d{3})\/(\d{4})/, '.$1/$2')
            .replace(/(\d{4})(\d)/, '/$1-$2');
    };

    const validateCNPJ = (cnpj: string) => {
        const digits = cnpj.replace(/\D/g, '');
        return digits.length === 14;
    };

    useEffect(() => {
        fetchTenants();
    }, []);

    async function fetchTenants() {
        try {
            const data = await api.get('/admin/tenants');
            const list = Array.isArray(data) ? data : [];
            setTenants(list);
            // Calcular MRR total localmente
            const mrr = list.reduce((acc: number, t: any) => acc + (t.billing?.monthly_value || 0), 0);
            setTotalMRR(mrr);
        } catch (error) {
            console.error("Failed to fetch tenants", error);
            setTenants([]);
        } finally {
            setLoading(false);
        }
    }

    const handleCreateTenant = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!validateCNPJ(newTenant.cnpj)) {
            alert("CNPJ inválido. Certifique-se de digitar os 14 dígitos.");
            return;
        }
        try {
            await api.post('/admin/tenants', { ...newTenant, cnpj: newTenant.cnpj.replace(/\D/g, '') });
            setIsModalOpen(false);
            setNewTenant({ nome: '', cnpj: '', plano: 'free' });
            fetchTenants();
        } catch (error) {
            // @ts-ignore
            alert(error.response?.data?.detail || "Erro ao criar escritório.");
        }
    };

    const [editingTenant, setEditingTenant] = useState<any>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [activeMenu, setActiveMenu] = useState<string | null>(null);

    const handleOpenEdit = (tenant: any) => { setEditingTenant({ ...tenant }); setIsEditModalOpen(true); setActiveMenu(null); };

    const handleUpdateTenant = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.put(`/admin/tenants/${editingTenant.id}`, editingTenant);
            setIsEditModalOpen(false);
            fetchTenants();
        } catch { alert("Erro ao atualizar escritório."); }
    };

    const handleDeleteTenant = async (tenant: any) => {
        if (!confirm(`CUIDADO: Isso excluirá permanentemente "${tenant.nome}" e TODOS os seus dados.`)) return;
        try {
            await api.delete(`/admin/tenants/${tenant.id}`);
            fetchTenants();
        } catch { alert("Erro ao excluir escritório."); }
    };

    const filteredTenants = tenants.filter(t =>
        t.nome?.toLowerCase().includes(searchTerm.toLowerCase()) || t.cnpj?.includes(searchTerm)
    );

    return (
        <div className="space-y-6 animate-in fade-in duration-500" onClick={() => setActiveMenu(null)}>

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-black text-white tracking-tight">Escritórios Parceiros (Tenants)</h1>
                    <p className="text-end-text-sec">Gerencie os escritórios de contabilidade cadastrados.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-end-accent hover:bg-end-accent/90 text-black px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-colors"
                >
                    <Plus size={18} /> Novo Escritório
                </button>
            </div>

            {/* MRR Summary Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-end-card border border-end-border rounded-lg p-4 col-span-2">
                    <div className="flex items-center gap-2 mb-1">
                        <TrendingUp size={14} className="text-end-accent" />
                        <span className="text-[10px] font-bold text-end-text-sec uppercase tracking-widest">MRR Estimado (Total)</span>
                    </div>
                    <div className="text-2xl font-black text-end-accent">
                        {loading ? '...' : `R$ ${totalMRR.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
                    </div>
                    <div className="text-[10px] text-end-text-sec mt-1">Baseado em modelo incremental por CNPJ</div>
                </div>
                <div className="bg-end-card border border-end-border rounded-lg p-4">
                    <div className="text-[10px] font-bold text-end-text-sec uppercase mb-1">Escritórios</div>
                    <div className="text-2xl font-black text-white">{tenants.length}</div>
                </div>
                <div className="bg-end-card border border-end-border rounded-lg p-4">
                    <div className="text-[10px] font-bold text-end-text-sec uppercase mb-1">CNPJs Totais</div>
                    <div className="text-2xl font-black text-white">
                        {tenants.reduce((acc, t) => acc + (t.billing?.cnpj_count || 0), 0)}
                    </div>
                </div>
            </div>

            {/* Search */}
            <div className="flex items-center gap-4 bg-white/5 p-4 rounded-xl border border-white/10">
                <Search className="text-end-text-sec" size={20} />
                <input
                    type="text"
                    placeholder="Buscar por nome ou CNPJ..."
                    className="bg-transparent border-none text-white placeholder-end-text-sec/50 outline-none w-full"
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                />
            </div>

            {/* Table */}
            <div className="bg-end-card border border-end-border rounded-xl overflow-visible">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-white/5 border-b border-white/10">
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Nome do Escritório</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">CNPJ</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">CNPJs Monitorados</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Faixa</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Valor/Mês</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Cadastro</th>
                            <th className="p-4 text-xs font-bold text-end-text-sec uppercase text-right">Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan={7} className="p-8 text-center text-end-text-sec animate-pulse">Carregando dados de billing...</td></tr>
                        ) : filteredTenants.length === 0 ? (
                            <tr><td colSpan={7} className="p-8 text-center text-end-text-sec">Nenhum escritório encontrado.</td></tr>
                        ) : filteredTenants.map((tenant) => {
                            const billing = tenant.billing || {};
                            const tierStyle = TIER_STYLES[billing.tier] || TIER_STYLES['Sem CNPJs'];
                            return (
                                <tr key={tenant.id} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors group">
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded bg-blue-500/20 flex items-center justify-center text-blue-500">
                                                <Building2 size={16} />
                                            </div>
                                            <span className="font-bold text-white">{tenant.nome}</span>
                                        </div>
                                    </td>
                                    <td className="p-4 text-end-text-sec font-mono text-sm">{tenant.cnpj}</td>

                                    {/* CNPJs Monitorados */}
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-24 bg-white/10 rounded-full h-1.5">
                                                <div
                                                    className="bg-end-accent h-1.5 rounded-full transition-all"
                                                    style={{ width: `${Math.min(100, (billing.cnpj_count || 0) / 50 * 100)}%` }}
                                                />
                                            </div>
                                            <span className="text-sm font-bold text-white">{billing.cnpj_count || 0}</span>
                                        </div>
                                    </td>

                                    {/* Faixa */}
                                    <td className="p-4">
                                        <span className={cn(
                                            "text-[10px] font-bold px-2 py-1 rounded uppercase",
                                            tierStyle.bg, tierStyle.text
                                        )}>
                                            {billing.tier || 'Sem CNPJs'}
                                        </span>
                                    </td>

                                    {/* Valor Mensal */}
                                    <td className="p-4">
                                        <div>
                                            <div className="text-white font-bold text-sm">
                                                {billing.monthly_value > 0
                                                    ? `R$ ${billing.monthly_value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                                                    : <span className="text-end-text-sec">—</span>
                                                }
                                            </div>
                                            {billing.rate_per_cnpj > 0 && (
                                                <div className="text-[10px] text-end-text-sec">
                                                    R$ {billing.rate_per_cnpj}/CNPJ
                                                </div>
                                            )}
                                        </div>
                                    </td>

                                    <td className="p-4 text-end-text-sec text-sm">
                                        {new Date(tenant.created_at).toLocaleDateString('pt-BR')}
                                    </td>

                                    <td className="p-4 text-right relative">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setActiveMenu(activeMenu === tenant.id ? null : tenant.id); }}
                                            className="p-2 text-end-text-sec hover:text-white transition-colors"
                                        >
                                            <MoreHorizontal size={18} />
                                        </button>
                                        {activeMenu === tenant.id && (
                                            <div className="absolute right-4 top-12 z-20 bg-end-card border border-end-border rounded-lg shadow-2xl py-2 w-48 animate-in zoom-in-95 duration-100">
                                                <button onClick={() => handleOpenEdit(tenant)} className="w-full px-4 py-2 text-sm text-white hover:bg-white/10 flex items-center gap-2">
                                                    <Edit2 size={14} className="text-blue-400" /> Editar Escritório
                                                </button>
                                                <button onClick={() => window.location.href = `/admin/users?tenant_id=${tenant.id}`} className="w-full px-4 py-2 text-sm text-white hover:bg-white/10 flex items-center gap-2">
                                                    <User size={14} className="text-green-400" /> Gerenciar Usuários
                                                </button>
                                                <div className="h-px bg-white/10 my-1" />
                                                <button onClick={() => handleDeleteTenant(tenant)} className="w-full px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2">
                                                    <Trash2 size={14} /> Excluir Escritório
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Modal Create */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-6 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-6">Novo Escritório</h2>
                        <form onSubmit={handleCreateTenant} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Razão Social</label>
                                <input type="text" value={newTenant.nome} onChange={e => setNewTenant({ ...newTenant, nome: e.target.value })} className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent" required />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">CNPJ do Escritório</label>
                                <input type="text" value={newTenant.cnpj} onChange={e => setNewTenant({ ...newTenant, cnpj: formatCNPJ(e.target.value) })} placeholder="00.000.000/0001-00" className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent" required />
                            </div>
                            <div className="flex gap-3 pt-4">
                                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 px-4 py-2 border border-white/10 rounded-lg text-end-text-sec hover:bg-white/5">Cancelar</button>
                                <button type="submit" className="flex-1 px-4 py-2 bg-end-accent text-black font-bold rounded-lg hover:bg-end-accent/90">Criar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal Edit */}
            {isEditModalOpen && editingTenant && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-6 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-6">Editar Escritório</h2>
                        <form onSubmit={handleUpdateTenant} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Razão Social</label>
                                <input type="text" value={editingTenant.nome} onChange={e => setEditingTenant({ ...editingTenant, nome: e.target.value })} className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent" required />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">CNPJ</label>
                                <input type="text" value={editingTenant.cnpj} onChange={e => setEditingTenant({ ...editingTenant, cnpj: formatCNPJ(e.target.value) })} className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent" required />
                            </div>
                            <div className="flex gap-3 pt-4">
                                <button type="button" onClick={() => setIsEditModalOpen(false)} className="flex-1 px-4 py-2 border border-white/10 rounded-lg text-end-text-sec hover:bg-white/5">Cancelar</button>
                                <button type="submit" className="flex-1 px-4 py-2 bg-end-accent text-black font-bold rounded-lg hover:bg-end-accent/90">Salvar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
