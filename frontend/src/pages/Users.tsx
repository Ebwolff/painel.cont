import React, { useEffect, useState } from 'react';
import { Plus, Search, User, Shield, Lock, Edit2, CheckCircle, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const PERMISSION_META = [
    { id: 'can_upload_xml', label: 'Upload de NF-e', description: 'Enviar arquivos XML' },
    { id: 'can_view_roi', label: 'Relatório de Valor', description: 'Ver indicadores ROI' },
    { id: 'can_resolve_alerts', label: 'Gestão de Alertas', description: 'Resolver inconformidades' },
    { id: 'can_manage_companies', label: 'Gestão de Clientes', description: 'Cadastrar/Editar empresas' },
    { id: 'can_manage_team', label: 'Gestão de Equipe', description: 'Gerenciar outros usuários' },
    { id: 'can_delete_data', label: 'Poder de Exclusão', description: 'Apagar registros sensíveis' },
];

export function Users() {
    const { user: currentUser } = useAuth();
    const [users, setUsers] = useState<any[]>([]);
    const [companies, setCompanies] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isPermModalOpen, setIsPermModalOpen] = useState(false);

    const [newUser, setNewUser] = useState({ nome: '', email: '', password: '', role: 'contador', empresa_id: '' });
    const [editingUser, setEditingUser] = useState<any>(null);
    const [permissions, setPermissions] = useState<Record<string, boolean>>({});

    useEffect(() => {
        fetchUsers();
        fetchCompanies();
    }, []);

    async function fetchUsers() {
        setLoading(true);
        try {
            const data = await api.get('/users/my-tenant');
            setUsers(data);
        } catch (error) {
            console.error("Failed to fetch users", error);
        } finally {
            setLoading(false);
        }
    }

    async function fetchCompanies() {
        try {
            const data = await api.get('/companies');
            setCompanies(data || []);
        } catch (error) {
            console.error("Failed to fetch companies", error);
        }
    }

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post('/users/my-tenant', newUser);
            setIsCreateModalOpen(false);
            setNewUser({ nome: '', email: '', password: '', role: 'contador', empresa_id: '' });
            fetchUsers();
            alert("Usuário criado com sucesso!");
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
            await api.put(`/users/${editingUser.id}/permissions`, { permissions });
            setIsPermModalOpen(false);
            fetchUsers();
            alert("Permissões atualizadas!");
        } catch (error) {
            console.error("Failed to update permissions", error);
            alert("Erro ao atualizar permissões.");
        }
    };

    const togglePermission = (key: string) => {
        setPermissions(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editFormData, setEditFormData] = useState({ id: '', nome: '', role: '', empresa_id: '' });

    // ... (existing code)

    const handleDeleteUser = async (user: any) => {
        if (!confirm(`Tem certeza que deseja excluir ${user.nome}?`)) return;
        try {
            await api.delete(`/users/${user.id}`);
            fetchUsers();
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
            empresa_id: user.empresa_id || ''
        });
        setIsEditModalOpen(true);
    };

    const handleUpdateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.put(`/users/${editFormData.id}`, {
                nome: editFormData.nome,
                role: editFormData.role,
                empresa_id: editFormData.empresa_id
            });
            setIsEditModalOpen(false);
            fetchUsers();
            alert("Usuário atualizado com sucesso!");
        } catch (error) {
            console.error("Failed to update user", error);
            // @ts-ignore
            const errorMessage = error.response?.data?.detail || "Erro ao atualizar usuário.";
            alert(errorMessage);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-black text-white tracking-tight">Equipe do Escritório</h1>
                    <p className="text-end-text-sec">Gerencie os acessos da sua contabilidade e clientes.</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="bg-end-accent hover:bg-end-accent/90 text-black px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-colors"
                >
                    <Plus size={18} /> Novo Acesso
                </button>
            </div>

            {/* Users List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <p className="text-white">Carregando...</p>
                ) : users.length === 0 ? (
                    <p className="text-end-text-sec">Nenhum usuário encontrado.</p>
                ) : (
                    users.map(user => (
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
                                {user.id !== currentUser?.id && (
                                    <button
                                        onClick={() => handleDeleteUser(user)}
                                        className="p-1.5 text-red-400 hover:bg-red-500/10 rounded"
                                        title="Excluir Usuário"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                )}
                            </div>

                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-black flex items-center justify-center border border-white/10 text-white font-bold">
                                        {user.nome?.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-white max-w-[150px] truncate" title={user.nome}>{user.nome}</h3>
                                        <p className="text-xs text-end-text-sec max-w-[150px] truncate" title={user.email}>{user.email}</p>
                                        {user.role === 'monitor' && user.empresa_id && (
                                            <p className="text-[10px] text-green-400 mt-1">
                                                Empresa: {companies.find(c => c.id === user.empresa_id)?.razao_social || '...'}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <span className={`text-[10px] font-bold px-2 py-1 rounded uppercase ${user.role === 'admin' ? 'bg-purple-500/20 text-purple-400' :
                                    user.role === 'monitor' ? 'bg-green-500/20 text-green-400' :
                                        'bg-blue-500/20 text-blue-400'
                                    }`}>
                                    {user.role === 'admin' ? 'Admin' : user.role === 'monitor' ? 'Monitor' : 'Contador'}
                                </span>
                            </div>

                            <div className="space-y-2 mb-6">
                                <p className="text-xs font-bold text-end-text-sec uppercase">Permissões</p>
                                <div className="flex flex-wrap gap-2">
                                    {user.permissions && Object.entries(user.permissions).map(([key, val]) => (
                                        val && (
                                            <span key={key} className="text-[10px] bg-white/5 text-gray-300 px-2 py-0.5 rounded border border-white/5">
                                                {key.replace('can_', '').replace('_', ' ')}
                                            </span>
                                        )
                                    ))}
                                    {(!user.permissions || Object.values(user.permissions).every(v => !v)) && (
                                        <span className="text-[10px] text-end-text-sec italic">Nenhuma</span>
                                    )}
                                </div>
                            </div>

                            {/* Só pode editar se não for ele mesmo (opcional) ou sempre */}
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
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-6 shadow-2xl">
                        <h3 className="text-xl font-bold text-white mb-6">Novo Acesso</h3>
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
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Senha Inicial</label>
                                <input
                                    type="text" // Visible for easy copying
                                    value={newUser.password}
                                    onChange={e => setNewUser({ ...newUser, password: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                    required
                                    placeholder="Ex: Mudar123!"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Tipo de Acesso</label>
                                <select
                                    value={newUser.role}
                                    onChange={e => setNewUser({ ...newUser, role: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                >
                                    <option value="contador">Contador (Operacional)</option>
                                    <option value="admin">Administrador (Gestão Total)</option>
                                    <option value="monitor">Cliente / Monitor (Acesso Limitado)</option>
                                </select>
                            </div>

                            {/* Company Selector for Monitor */}
                            {newUser.role === 'monitor' && (
                                <div className="animate-in fade-in slide-in-from-top-2 duration-300">
                                    <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Empresa Vinculada</label>
                                    <select
                                        value={newUser.empresa_id}
                                        onChange={e => setNewUser({ ...newUser, empresa_id: e.target.value })}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                        required
                                    >
                                        <option value="" disabled>Selecione a empresa do cliente...</option>
                                        {companies.map(c => (
                                            <option key={c.id} value={c.id}>{c.razao_social} ({c.cnpj})</option>
                                        ))}
                                    </select>
                                    {companies.length === 0 && (
                                        <p className="text-xs text-red-400 mt-1">Nenhuma empresa cadastrada. Cadastre uma empresa antes.</p>
                                    )}
                                </div>
                            )}

                            <div className="flex gap-3 pt-4">
                                <button type="button" onClick={() => setIsCreateModalOpen(false)} className="flex-1 px-4 py-2 border border-white/10 rounded-lg text-end-text-sec hover:bg-white/5">Cancelar</button>
                                <button type="submit" className="flex-1 px-4 py-2 bg-end-accent text-black font-bold rounded-lg hover:bg-end-accent/90">Criar Acesso</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Edit User Modal */}
            {isEditModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-6 shadow-2xl">
                        <h3 className="text-xl font-bold text-white mb-6">Editar Acesso</h3>
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
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Tipo de Acesso</label>
                                <select
                                    value={editFormData.role}
                                    onChange={e => setEditFormData({ ...editFormData, role: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                >
                                    <option value="contador">Contador</option>
                                    <option value="admin">Administrador</option>
                                    <option value="monitor">Cliente / Monitor</option>
                                </select>
                            </div>

                            {editFormData.role === 'monitor' && (
                                <div className="animate-in fade-in slide-in-from-top-2 duration-300">
                                    <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Empresa Vinculada</label>
                                    <select
                                        value={editFormData.empresa_id}
                                        onChange={e => setEditFormData({ ...editFormData, empresa_id: e.target.value })}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white outline-none focus:border-end-accent"
                                        required
                                    >
                                        <option value="" disabled>Selecione a empresa...</option>
                                        {companies.map(c => (
                                            <option key={c.id} value={c.id}>{c.razao_social}</option>
                                        ))}
                                    </select>
                                </div>
                            )}

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
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-6 shadow-2xl">
                        <h3 className="text-xl font-bold text-white mb-2">Permissões de {editingUser.nome}</h3>
                        <p className="text-sm text-end-text-sec mb-6">O que este usuário pode fazer?</p>

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
                                <CheckCircle size={18} /> Salvar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
