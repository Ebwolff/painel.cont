import React, { useEffect, useState } from 'react';
import { Plus, Search, User, Shield, Lock, Edit2, CheckCircle, Trash2 } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { api } from '../../services/api';

const PERMISSION_META = [
    { id: 'can_upload_xml', label: 'Upload de NF-e', description: 'Enviar arquivos XML' },
    { id: 'can_view_roi', label: 'Relatório de Valor', description: 'Ver indicadores ROI' },
    { id: 'can_resolve_alerts', label: 'Gestão de Alertas', description: 'Resolver inconformidades' },
    { id: 'can_manage_companies', label: 'Gestão de Clientes', description: 'Cadastrar/Editar empresas' },
    { id: 'can_manage_team', label: 'Gestão de Equipe', description: 'Gerenciar outros usuários' },
    { id: 'can_delete_data', label: 'Poder de Exclusão', description: 'Apagar registros sensíveis' },
];

export function UsersList() {
    const [users, setUsers] = useState<any[]>([]);
    const [tenants, setTenants] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedTenant, setSelectedTenant] = useState<string>('');
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isPermModalOpen, setIsPermModalOpen] = useState(false);

    const [newUser, setNewUser] = useState({ nome: '', email: '', password: '', role: 'contador' });
    const [editingUser, setEditingUser] = useState<any>(null);
    const [userSearch, setUserSearch] = useState('');
    const [permissions, setPermissions] = useState<Record<string, boolean>>({});

    const location = useLocation();

    useEffect(() => {
        fetchTenants();

        // Verificar se há tenant_id na URL
        const params = new URLSearchParams(location.search);
        const tenantIdParam = params.get('tenant_id');
        if (tenantIdParam) {
            setSelectedTenant(tenantIdParam);
        }
    }, [location.search]);

    useEffect(() => {
        if (selectedTenant) {
            fetchUsers(selectedTenant);
        } else if (tenants.length > 0 && !new URLSearchParams(location.search).get('tenant_id')) {
            setSelectedTenant(tenants[0].id);
        }
    }, [selectedTenant, tenants, location.search]);

    async function fetchTenants() {
        try {
            const data = await api.get('/admin/tenants');
            setTenants(data);
        } catch (error) {
            console.error("Failed to fetch tenants", error);
        }
    }

    async function fetchUsers(tenantId: string) {
        setLoading(true);
        try {
            const data = await api.get(`/admin/users/${tenantId}`);
            setUsers(data);
        } catch (error) {
            console.error("Failed to fetch users", error);
        } finally {
            setLoading(false);
        }
    }

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post('/admin/users', { ...newUser, tenant_id: selectedTenant });
            setIsCreateModalOpen(false);
            setNewUser({ nome: '', email: '', password: '', role: 'contador' });
            fetchUsers(selectedTenant);
        } catch (error) {
            console.error("Failed to create user", error);
            // @ts-ignore
            const errorMessage = error.response?.data?.detail || "Erro ao criar usuário.";
            alert(errorMessage);
        }
    };

    const handleOpenPermModal = (user: any) => {
        setEditingUser(user);

        // Inicializar todas as permissões do meta como false, sobrescrevendo com as que o usuário já tem
        const initialPerms: Record<string, boolean> = {};
        PERMISSION_META.forEach(p => {
            initialPerms[p.id] = !!(user.permissions && user.permissions[p.id]);
        });

        setPermissions(initialPerms);
        setIsPermModalOpen(true);
    };

    const handleSavePermissions = async () => {
        if (!editingUser) return;
        try {
            await api.put(`/admin/users/${editingUser.id}/permissions`, { permissions });
            setIsPermModalOpen(false);
            fetchUsers(selectedTenant);
        } catch (error) {
            console.error("Failed to update permissions", error);
            alert("Erro ao atualizar permissões.");
        }
    };

    const togglePermission = (key: string) => {
        setPermissions(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editFormData, setEditFormData] = useState({ id: '', nome: '', role: '', tenant_id: '' });

    // ... (existing code)

    const handleDeleteUser = async (user: any) => {
        if (!confirm(`Tem certeza que deseja excluir ${user.nome}?`)) return;
        try {
            await api.delete(`/admin/users/${user.id}`);
            fetchUsers(selectedTenant);
        } catch (error) {
            console.error("Failed to delete user", error);
            // @ts-ignore
            const errorMessage = error.response?.data?.detail || "Erro ao excluir usuário.";
            alert(errorMessage);
        }
    };

    const handleOpenEditModal = (user: any) => {
        setEditFormData({
            id: user.id,
            nome: user.nome || '',
            role: user.role || 'contador',
            tenant_id: user.tenant_id
        });
        setIsEditModalOpen(true);
    };

    const handleUpdateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.put(`/admin/users/${editFormData.id}`, {
                nome: editFormData.nome,
                role: editFormData.role,
                tenant_id: editFormData.tenant_id
            });
            setIsEditModalOpen(false);
            fetchUsers(selectedTenant);
        } catch (error) {
            console.error("Failed to update user", error);
            // @ts-ignore
            const errorMessage = error.response?.data?.detail || "Erro ao atualizar usuário.";
            alert(errorMessage);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* ... (Header and Tenant Selector) ... */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-black text-white tracking-tight">Gestão de Usuários</h1>
                    <p className="text-end-text-sec">Gerencie acessos e permissões por escritório.</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    disabled={!selectedTenant}
                    className="bg-end-accent hover:bg-end-accent/90 text-black px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-colors disabled:opacity-50"
                >
                    <Plus size={18} /> Novo Usuário
                </button>
            </div>

            {/* Tenant Selector & Search */}
            <div className="flex flex-col md:flex-row gap-4 mb-6">
                <div className="flex-1 bg-white/5 p-4 rounded-xl border border-white/10">
                    <label className="block text-[10px] font-bold text-end-text-sec uppercase mb-2 tracking-widest">Escritório Parceiro</label>
                    <select
                        value={selectedTenant}
                        onChange={e => setSelectedTenant(e.target.value)}
                        className="w-full bg-transparent text-lg font-black text-white outline-none appearance-none cursor-pointer"
                    >
                        <option value="" disabled className="bg-end-card text-white">Selecione um escritório...</option>
                        {tenants.map(t => (
                            <option key={t.id} value={t.id} className="bg-end-card text-white">{t.nome} ({t.cnpj})</option>
                        ))}
                    </select>
                </div>

                <div className="flex-[2] bg-white/5 p-4 rounded-xl border border-white/10 flex items-center gap-3">
                    <Search className="text-end-text-sec" size={20} />
                    <input
                        type="text"
                        placeholder="Buscar por nome ou email nestes usuários..."
                        className="bg-transparent border-none text-white placeholder-end-text-sec/40 outline-none w-full"
                        value={userSearch}
                        onChange={e => setUserSearch(e.target.value)}
                    />
                </div>
            </div>

            {/* Users List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <p className="text-white">Carregando usuários...</p>
                ) : users.filter(u =>
                    u.nome?.toLowerCase().includes(userSearch.toLowerCase()) ||
                    u.email?.toLowerCase().includes(userSearch.toLowerCase())
                ).length === 0 ? (
                    <p className="text-end-text-sec">Nenhum usuário encontrado com este critério.</p>
                ) : (
                    users.filter(u =>
                        u.nome?.toLowerCase().includes(userSearch.toLowerCase()) ||
                        u.email?.toLowerCase().includes(userSearch.toLowerCase())
                    ).map(user => (
                        <div key={user.id} className="bg-end-card border border-end-border rounded-xl p-6 relative group hover:border-end-accent/50 transition-colors">
                            {/* Actions Top Right */}
                            <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={() => handleOpenEditModal(user)}
                                    className="p-1.5 text-blue-400 hover:bg-blue-500/10 rounded"
                                    title="Editar Dados"
                                >
                                    <Edit2 size={16} />
                                </button>
                                <button
                                    onClick={() => handleDeleteUser(user)}
                                    className="p-1.5 text-red-400 hover:bg-red-500/10 rounded"
                                    title="Excluir Usuário"
                                >
                                    <Trash2 size={16} /> {/* Must import Trash2 if not imported */}
                                </button>
                            </div>

                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-black flex items-center justify-center border border-white/10 text-white font-bold">
                                        {user.nome?.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                        <p className="font-bold text-white">{user.nome}</p>
                                        <p className="text-xs text-end-text-sec">{user.email}</p>
                                    </div>
                                </div>
                                <span className={`text-[10px] font-bold px-2 py-1 rounded uppercase ${user.role === 'admin' ? 'bg-teal-500/20 text-teal-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                    {user.role}
                                </span>
                            </div>

                            <div className="space-y-2 mb-6">
                                <p className="text-xs font-bold text-end-text-sec uppercase">Permissões Ativas</p>
                                <div className="flex flex-wrap gap-2">
                                    {user.permissions && Object.entries(user.permissions).map(([key, val]) => (
                                        val && (
                                            <span key={key} className="text-[10px] bg-white/5 text-gray-300 px-2 py-0.5 rounded border border-white/5">
                                                {key.replace('can_', '').replace('_', ' ')}
                                            </span>
                                        )
                                    ))}
                                    {(!user.permissions || Object.values(user.permissions).every(v => !v)) && (
                                        <span className="text-[10px] text-end-text-sec italic">Nenhuma permissão especial</span>
                                    )}
                                </div>
                            </div>

                            <button
                                onClick={() => handleOpenPermModal(user)}
                                className="w-full py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white font-medium flex items-center justify-center gap-2 transition-colors"
                            >
                                <Shield size={14} /> Gerenciar Permissões
                            </button>
                        </div>
                    ))
                )}
            </div>

            {/* Create User Modal */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-6 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-6">Novo Usuário</h2>
                        <form onSubmit={handleCreateUser} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Nome Completo</label>
                                <input
                                    type="text"
                                    value={newUser.nome}
                                    onChange={e => setNewUser({ ...newUser, nome: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Email</label>
                                <input
                                    type="email"
                                    value={newUser.email}
                                    onChange={e => setNewUser({ ...newUser, email: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Senha Temporária</label>
                                <input
                                    type="password"
                                    value={newUser.password}
                                    onChange={e => setNewUser({ ...newUser, password: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Nível de Acesso</label>
                                <select
                                    value={newUser.role}
                                    onChange={e => setNewUser({ ...newUser, role: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                >
                                    <option value="contador">Contador (Padrão)</option>
                                    <option value="admin">Administrador do Tenant</option>
                                </select>
                            </div>
                            <div className="flex gap-3 pt-4">
                                <button type="button" onClick={() => setIsCreateModalOpen(false)} className="flex-1 px-4 py-2 border border-white/10 rounded-lg text-end-text-sec hover:bg-white/5">Cancelar</button>
                                <button type="submit" className="flex-1 px-4 py-2 bg-end-accent text-black font-bold rounded-lg hover:bg-end-accent/90">Criar Usuário</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Edit User Modal */}
            {isEditModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-6 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-6">Editar Usuário</h2>
                        <form onSubmit={handleUpdateUser} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Nome Completo</label>
                                <input
                                    type="text"
                                    value={editFormData.nome}
                                    onChange={e => setEditFormData({ ...editFormData, nome: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                    required
                                />
                            </div>
                            {/* Role */}
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Nível de Acesso</label>
                                <select
                                    value={editFormData.role}
                                    onChange={e => setEditFormData({ ...editFormData, role: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                >
                                    <option value="contador">Contador</option>
                                    <option value="admin">Administrador</option>
                                    <option value="super_admin">Super Admin</option>
                                </select>
                            </div>
                            {/* Tenant Transfer (Optional for Super Admin) */}
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Escritório (Transferência)</label>
                                <select
                                    value={editFormData.tenant_id}
                                    onChange={e => setEditFormData({ ...editFormData, tenant_id: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                >
                                    {tenants.map(t => (
                                        <option key={t.id} value={t.id}>{t.nome}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button type="button" onClick={() => setIsEditModalOpen(false)} className="flex-1 px-4 py-2 border border-white/10 rounded-lg text-end-text-sec hover:bg-white/5">Cancelar</button>
                                <button type="submit" className="flex-1 px-4 py-2 bg-blue-500 text-white font-bold rounded-lg hover:bg-blue-600">Salvar Alterações</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Permissions Modal */}
            {isPermModalOpen && editingUser && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-6 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-2">Permissões de Acesso</h2>
                        <p className="text-sm text-end-text-sec mb-6">Defina o que <strong>{editingUser.nome}</strong> pode fazer.</p>

                        <div className="space-y-2 mb-6 max-h-[400px] overflow-y-auto pr-2">
                            {PERMISSION_META.map(perm => {
                                const checked = permissions[perm.id];
                                return (
                                    <label key={perm.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 border border-transparent hover:border-white/10 transition-all">
                                        <div className="flex flex-col">
                                            <span className="text-sm text-white font-bold">{perm.label}</span>
                                            <span className="text-[10px] text-end-text-sec uppercase tracking-tight">{perm.description}</span>
                                        </div>
                                        <div className="relative">
                                            <input
                                                type="checkbox"
                                                checked={!!checked}
                                                onChange={() => togglePermission(perm.id)}
                                                className="sr-only peer"
                                            />
                                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-end-accent"></div>
                                        </div>
                                    </label>
                                );
                            })}
                        </div>

                        <div className="flex gap-3">
                            <button type="button" onClick={() => setIsPermModalOpen(false)} className="flex-1 px-4 py-2 border border-white/10 rounded-lg text-end-text-sec hover:bg-white/5">Cancelar</button>
                            <button type="button" onClick={handleSavePermissions} className="flex-1 px-4 py-2 bg-green-500 text-white font-bold rounded-lg hover:bg-green-600 flex items-center justify-center gap-2">
                                <CheckCircle size={18} /> Salvar Alterações
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
