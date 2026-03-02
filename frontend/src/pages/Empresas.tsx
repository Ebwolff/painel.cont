import React, { useEffect, useState } from 'react';
import { Building2, MoreVertical, ShieldCheck, ShieldAlert, RefreshCw, Key, Trash2, Star, Lock } from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useFeatures } from '../hooks/useFeatures';
import { useNavigate } from 'react-router-dom';

export function Empresas() {
    const navigate = useNavigate();
    const { hasPermission } = useAuth();
    const { hasFeature, tier } = useFeatures();
    const [companies, setCompanies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const [syncing, setSyncing] = useState<string | null>(null);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [newCompany, setNewCompany] = useState({
        razao_social: '',
        cnpj: '',
        regime_tributario: 'lucro_real'
    });

    const [isCertModalOpen, setIsCertModalOpen] = useState(false);
    const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
    const [certFile, setCertFile] = useState<File | null>(null);
    const [certPassword, setCertPassword] = useState('');
    const [certAmbiente, setCertAmbiente] = useState<'producao' | 'homologacao'>('producao');
    const [certUploadResult, setCertUploadResult] = useState<{ expires_at: string; dias_restantes: number; ambiente: string } | null>(null);
    const [certUploadError, setCertUploadError] = useState<string | null>(null);
    const [isUploadingCert, setIsUploadingCert] = useState(false);
    const [openMenuId, setOpenMenuId] = useState<string | null>(null);

    const formatCNPJ = (value: string) => {
        const digits = value.replace(/\D/g, '').slice(0, 14);
        return digits
            .replace(/^(\d{2})(\d)/, '$1.$2')
            .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
            .replace(/\.(\d{3})(\d)/, '.$1/$2')
            .replace(/\/(\d{4})(\d)/, '/$1-$2');
    };

    const validateCNPJ = (cnpj: string) => {
        const digits = cnpj.replace(/\D/g, '');
        return digits.length === 14;
    };

    useEffect(() => {
        fetchCompanies();
    }, []);

    async function fetchCompanies() {
        setLoading(true);
        try {
            const data = await api.get('/companies/');
            setCompanies(data);
        } catch (error) {
            console.error("Failed to fetch companies", error);
        } finally {
            setLoading(false);
        }
    }

    const handleCertUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedCompany || !certFile) return;

        setIsUploadingCert(true);
        setCertUploadError(null);
        setCertUploadResult(null);

        const formData = new FormData();
        formData.append('file', certFile);
        formData.append('password', certPassword);
        formData.append('ambiente', certAmbiente);

        try {
            const result = await api.upload(`/certificates/upload/${selectedCompany}`, formData);
            setCertUploadResult(result);
            fetchCompanies();
        } catch (error: any) {
            setCertUploadError(error.message || 'Erro ao enviar certificado.');
        } finally {
            setIsUploadingCert(false);
        }
    };

    const closeCertModal = () => {
        setIsCertModalOpen(false);
        setCertFile(null);
        setCertPassword('');
        setCertAmbiente('producao');
        setCertUploadResult(null);
        setCertUploadError(null);
    };

    const [editingCompanyId, setEditingCompanyId] = useState<string | null>(null);

    const openEditModal = (empresa: any) => {
        setEditingCompanyId(empresa.id);
        setNewCompany({
            razao_social: empresa.razao_social,
            cnpj: formatCNPJ(empresa.cnpj),
            regime_tributario: empresa.regime_tributario || 'lucro_real'
        });
        setIsModalOpen(true);
        setOpenMenuId(null);
    };

    const handleCreateOrEditCompany = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateCNPJ(newCompany.cnpj)) {
            alert("CNPJ inválido. Certifique-se de digitar os 14 dígitos.");
            return;
        }

        setIsSaving(true);
        try {
            if (editingCompanyId) {
                await api.put(`/companies/${editingCompanyId}`, newCompany);
                alert("Empresa atualizada com sucesso!");
            } else {
                await api.post('/companies/', newCompany);
                alert("Empresa cadastrada com sucesso!");
            }
            setIsModalOpen(false);
            setEditingCompanyId(null);
            setNewCompany({ razao_social: '', cnpj: '', regime_tributario: 'lucro_real' });
            fetchCompanies();
        } catch (error: any) {
            console.error("Failed to save company", error);
            alert(error.message || "Erro ao salvar empresa. Verifique os dados.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleSync = async (companyId: string) => {
        setSyncing(companyId);
        try {
            await api.post(`/sefaz/trigger/${companyId}`, {});
            alert("Sincronização com SEFAZ iniciada com sucesso!");
        } catch (error) {
            console.error("Sync failed", error);
        } finally {
            setSyncing(null);
        }
    };

    const handleDelete = async (companyId: string) => {
        if (!confirm('Tem certeza que deseja excluir esta empresa? Esta ação é irreversível e apagará todos os dados fiscais vinculados.')) {
            return;
        }

        try {
            await api.delete(`/companies/${companyId}`);
            alert('Empresa removida com sucesso.');
            fetchCompanies();
        } catch (error) {
            console.error("Delete failed", error);
            alert('Erro ao excluir empresa. Verifique se você tem permissão.');
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">Gestão de Empresas</h2>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-end-accent hover:bg-end-accent/90 text-black px-4 py-2 rounded-md text-sm font-bold transition-colors"
                >
                    Nova Empresa
                </button>
            </div>

            {/* Modal Nova Empresa */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-end-card border border-end-border w-full max-w-md rounded-xl p-8 shadow-2xl">
                        <h3 className="text-xl font-bold text-white mb-6">
                            {editingCompanyId ? 'Editar Empresa' : 'Cadastrar Nova Empresa'}
                        </h3>
                        <form onSubmit={handleCreateOrEditCompany} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Razão Social</label>
                                <input
                                    type="text"
                                    value={newCompany.razao_social}
                                    onChange={e => setNewCompany({ ...newCompany, razao_social: e.target.value })}
                                    placeholder="Ex: Minha Empresa LTDA"
                                    className="w-full bg-end-bg border border-end-border rounded p-2 text-white outline-none focus:border-end-accent"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">CNPJ</label>
                                <input
                                    type="text"
                                    value={newCompany.cnpj}
                                    onChange={e => setNewCompany({ ...newCompany, cnpj: formatCNPJ(e.target.value) })}
                                    placeholder="00.000.000/0001-00"
                                    className="w-full bg-end-bg border border-end-border rounded p-2 text-white outline-none focus:border-end-accent"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Regime Tributário</label>
                                <select
                                    value={newCompany.regime_tributario}
                                    onChange={e => setNewCompany({ ...newCompany, regime_tributario: e.target.value })}
                                    className="w-full bg-end-bg border border-end-border rounded p-2 text-white outline-none focus:border-end-accent"
                                >
                                    <option value="simples_nacional">Simples Nacional</option>
                                    <option value="lucro_presumido">Lucro Presumido</option>
                                    <option value="lucro_real">Lucro Real</option>
                                </select>
                            </div>
                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsModalOpen(false);
                                        setEditingCompanyId(null);
                                        setNewCompany({ razao_social: '', cnpj: '', regime_tributario: 'lucro_real' });
                                    }}
                                    className="flex-1 px-4 py-2 border border-end-border rounded text-end-text-sec hover:bg-white/5 transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSaving}
                                    className={cn(
                                        "flex-1 px-4 py-2 bg-end-accent text-black font-bold rounded hover:bg-end-accent/90 transition-colors flex items-center justify-center gap-2",
                                        isSaving && "opacity-50 cursor-not-allowed"
                                    )}
                                >
                                    {isSaving ? (
                                        <>
                                            <RefreshCw size={16} className="animate-spin" />
                                            Salvando...
                                        </>
                                    ) : (editingCompanyId ? "Salvar Alterações" : "Salvar Empresa")}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal Certificado A1 */}
            {isCertModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-end-card border border-end-border w-full max-w-sm rounded-xl p-8 shadow-2xl">
                        <h3 className="text-xl font-bold text-white mb-1">Certificado A1</h3>
                        <p className="text-xs text-end-text-sec mb-6">Necessário para busca automática de NF-es na SEFAZ.</p>

                        {certUploadResult ? (
                            <div className="space-y-4">
                                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-center">
                                    <ShieldCheck size={32} className="text-green-400 mx-auto mb-2" />
                                    <p className="text-green-400 font-bold text-sm">Certificado configurado!</p>
                                    <p className="text-xs text-end-text-sec mt-1">
                                        Vence em: {new Date(certUploadResult.expires_at).toLocaleDateString('pt-BR')}
                                        {' '}({certUploadResult.dias_restantes} dias)
                                    </p>
                                    <p className="text-xs text-end-text-sec">
                                        Ambiente: <strong className="text-white">{certUploadResult.ambiente === 'producao' ? '🟢 Produção' : '🔵 Homologação'}</strong>
                                    </p>
                                </div>
                                <button
                                    onClick={closeCertModal}
                                    className="w-full py-3 bg-end-accent text-black font-bold rounded-xl hover:bg-end-accent/90 transition-colors"
                                >
                                    Concluir
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handleCertUpload} className="space-y-4">
                                {certUploadError && (
                                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                                        <p className="text-red-400 text-xs font-bold">⚠️ {certUploadError}</p>
                                    </div>
                                )}
                                <div>
                                    <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Arquivo .PFX ou .P12</label>
                                    <input
                                        type="file"
                                        accept=".pfx,.p12"
                                        onChange={e => setCertFile(e.target.files?.[0] || null)}
                                        className="w-full bg-end-bg border border-end-border rounded p-2 text-white text-sm"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Senha do Certificado</label>
                                    <input
                                        type="password"
                                        value={certPassword}
                                        onChange={e => setCertPassword(e.target.value)}
                                        placeholder="Senha gerada pela AC"
                                        className="w-full bg-end-bg border border-end-border rounded p-2 text-white outline-none focus:border-end-accent"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-end-text-sec uppercase mb-1">Ambiente SEFAZ</label>
                                    <select
                                        value={certAmbiente}
                                        onChange={e => setCertAmbiente(e.target.value as 'producao' | 'homologacao')}
                                        className="w-full bg-end-bg border border-end-border rounded p-2 text-white outline-none focus:border-end-accent"
                                    >
                                        <option value="producao">🟢 Produção (real)</option>
                                        <option value="homologacao">🔵 Homologação (teste)</option>
                                    </select>
                                </div>
                                <div className="flex gap-3 pt-2">
                                    <button
                                        type="button"
                                        onClick={closeCertModal}
                                        className="flex-1 px-4 py-2 border border-end-border rounded text-end-text-sec hover:bg-white/5 transition-colors"
                                    >
                                        Cancelar
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={isUploadingCert}
                                        className={cn(
                                            "flex-1 px-4 py-2 bg-end-accent text-black font-bold rounded hover:bg-end-accent/90 transition-colors flex items-center justify-center gap-2",
                                            isUploadingCert && "opacity-50 cursor-wait"
                                        )}
                                    >
                                        {isUploadingCert ? <><RefreshCw size={14} className="animate-spin" /> Validando...</> : 'Salvar Certificado'}
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <div className="col-span-full py-12 text-center text-end-text-sec animate-pulse">
                        Carregando empresas...
                    </div>
                ) : companies.length === 0 ? (
                    <div className="col-span-full py-20 text-center bg-end-card border border-end-border rounded-xl">
                        <p className="text-end-text-sec">Nenhuma empresa cadastrada. Comece adicionando sua primeira cliente.</p>
                    </div>
                ) : (
                    companies.map((empresa) => (
                        <div key={empresa.id} className="bg-end-card border border-end-border rounded-xl p-6 hover:shadow-lg hover:shadow-end-accent/5 transition-all group">
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-2 bg-end-bg rounded-lg group-hover:bg-end-accent/10 transition-colors">
                                    <Building2 className="text-end-accent" size={24} />
                                </div>
                                <div className="relative">
                                    <button
                                        onClick={() => setOpenMenuId(openMenuId === empresa.id ? null : empresa.id)}
                                        className="text-end-text-sec hover:text-white p-1 transition-colors"
                                    >
                                        <MoreVertical size={20} />
                                    </button>

                                    {openMenuId === empresa.id && (
                                        <>
                                            <div className="fixed inset-0 z-40" onClick={() => setOpenMenuId(null)} />
                                            <div className="absolute right-0 top-8 z-50 bg-end-card border border-end-border rounded-lg shadow-xl shadow-black/40 py-1 min-w-[180px] animate-in fade-in slide-in-from-top-2 duration-150">
                                                <button
                                                    onClick={() => openEditModal(empresa)}
                                                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-white hover:bg-white/5 transition-colors"
                                                >
                                                    <Building2 size={14} className="text-end-accent" /> Editar Empresa
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        setOpenMenuId(null);
                                                        setSelectedCompany(empresa.id);
                                                        setIsCertModalOpen(true);
                                                    }}
                                                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-white hover:bg-white/5 transition-colors"
                                                >
                                                    <Key size={14} className="text-end-accent" /> Certificado A1
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        setOpenMenuId(null);
                                                        handleSync(empresa.id);
                                                    }}
                                                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-white hover:bg-white/5 transition-colors"
                                                >
                                                    <RefreshCw size={14} className="text-end-accent" /> Sincronizar SEFAZ
                                                </button>
                                                <div className="border-t border-end-border my-1" />
                                                <button
                                                    onClick={() => {
                                                        setOpenMenuId(null);
                                                        handleDelete(empresa.id);
                                                    }}
                                                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-end-error hover:bg-end-error/10 transition-colors"
                                                >
                                                    <Trash2 size={14} /> Excluir Empresa
                                                </button>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="mb-6">
                                <h3 className="font-bold text-white truncate">{empresa.razao_social}</h3>
                                <p className="text-sm text-end-text-sec">{empresa.cnpj}</p>
                            </div>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-end-text-sec uppercase font-bold tracking-wider">Status Fiscal</span>
                                    <span className="text-white font-medium">
                                        {empresa.regime_tributario === 'simples_nacional' ? 'Simples Nacional' :
                                            empresa.regime_tributario === 'lucro_presumido' ? 'Lucro Presumido' : 'Lucro Real'}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-1.5 text-end-success font-medium text-xs">
                                        <ShieldCheck size={14} /> Regular
                                    </div>
                                </div>
                            </div>

                            <div className="mt-6 pt-6 border-t border-end-border grid grid-cols-2 gap-3">
                                <button
                                    onClick={() => {
                                        if (!hasFeature('sefaz_sync')) {
                                            navigate('/planos');
                                            return;
                                        }
                                        handleSync(empresa.id);
                                    }}
                                    disabled={syncing === empresa.id}
                                    className={cn(
                                        "flex items-center justify-center gap-2 py-2 rounded border border-end-border text-[10px] font-black uppercase transition-all",
                                        syncing === empresa.id ? "bg-white/5 opacity-50 cursor-not-allowed" :
                                            !hasFeature('sefaz_sync') ? "bg-white/5 text-end-text-sec opacity-60 hover:border-end-accent" :
                                                "bg-white/5 hover:bg-end-accent hover:text-black hover:border-end-accent"
                                    )}
                                >
                                    {syncing === empresa.id ? <RefreshCw size={12} className="animate-spin" /> :
                                        !hasFeature('sefaz_sync') ? <Lock size={12} className="text-end-accent" /> : <RefreshCw size={12} />}
                                    {syncing === empresa.id ? "Sinc..." : "SEFAZ Sync"}
                                </button>

                                <button
                                    onClick={() => {
                                        if (!hasFeature('sefaz_sync')) {
                                            navigate('/planos');
                                            return;
                                        }
                                        setSelectedCompany(empresa.id);
                                        setIsCertModalOpen(true);
                                    }}
                                    className={cn(
                                        "flex items-center justify-center gap-2 py-2 rounded border border-end-border text-[10px] font-black uppercase transition-all",
                                        empresa.servico_sefaz_ativo ? "bg-end-success/20 text-end-success border-end-success/30 hover:bg-end-success/30" :
                                            !hasFeature('sefaz_sync') ? "bg-white/5 text-end-text-sec opacity-60 hover:border-end-accent" :
                                                "bg-white/5 hover:bg-white/10"
                                    )}
                                >
                                    {!hasFeature('sefaz_sync') ? <Lock size={12} className="text-end-accent" /> : <Key size={12} />}
                                    {empresa.servico_sefaz_ativo ? "Certificado Ok" : "Add Certificado"}
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
