import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { ShieldCheck, RefreshCcw, Search, AlertCircle, Edit2, Check, X } from 'lucide-react';
import { cn } from '../../lib/utils';

export function RegrasFiscais() {
    const [rules, setRules] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);
    const [search, setSearch] = useState('');
    const [editingRule, setEditingRule] = useState<any>(null);

    useEffect(() => {
        fetchRules();
    }, []);

    async function fetchRules() {
        setLoading(true);
        try {
            const data = await api.get('/admin/rules/');
            setRules(data);
        } catch (error) {
            console.error("Erro ao carregar regras:", error);
        } finally {
            setLoading(false);
        }
    }

    async function handleSync() {
        setSyncing(true);
        try {
            const result = await api.post('/admin/rules/sync', {});
            alert(`Sincronização concluída! Criadas: ${result.created}, Atualizadas: ${result.updated}`);
            fetchRules();
        } catch (error) {
            alert("Erro na sincronização externa.");
        } finally {
            setSyncing(false);
        }
    }

    const filteredRules = rules.filter(r =>
        r.name?.toLowerCase().includes(search.toLowerCase()) ||
        r.ncm?.includes(search) ||
        r.cfop?.includes(search)
    );

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        Regras Fiscais (Inteligência 2.0)
                        <span className="text-[10px] bg-end-accent/20 text-end-accent px-2 py-0.5 rounded-full font-black uppercase">Alpha</span>
                    </h2>
                    <p className="text-sm text-end-text-sec italic">Gestão centralizada da Tabela da Verdade (CBS/IBS).</p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleSync}
                        disabled={syncing}
                        className={cn(
                            "flex items-center gap-2 bg-end-accent text-black px-4 py-2 rounded-md font-bold text-sm transition-all hover:scale-105 active:scale-95 disabled:opacity-50",
                            syncing && "animate-pulse"
                        )}
                    >
                        <RefreshCcw size={18} className={syncing ? "animate-spin" : ""} />
                        {syncing ? "Sincronizando..." : "Sincronizar com Fontes Federais"}
                    </button>
                </div>
            </div>

            <div className="bg-end-card border border-end-border rounded-lg overflow-hidden">
                <div className="p-4 border-b border-end-border bg-white/[0.02]">
                    <div className="relative max-w-sm">
                        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-end-text-sec" />
                        <input
                            type="text"
                            placeholder="Buscar por NCM, CFOP ou Nome..."
                            className="bg-black/20 border border-end-border rounded-md pl-10 pr-4 py-2 text-sm text-white w-full focus:outline-none focus:border-end-accent"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-white/5 border-b border-end-border">
                                <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Regra / Descrição</th>
                                <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Alvo (NCM/CFOP)</th>
                                <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Tipo</th>
                                <th className="p-4 text-xs font-bold text-end-text-sec uppercase">UF</th>
                                <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Alíquota</th>
                                <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Status</th>
                                <th className="p-4 text-xs font-bold text-end-text-sec uppercase">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan={6} className="p-8 text-center text-end-text-sec animate-pulse">Consultando motor de regras...</td></tr>
                            ) : filteredRules.length === 0 ? (
                                <tr><td colSpan={6} className="p-8 text-center text-end-text-sec">Nenhuma regra ativa encontrada.</td></tr>
                            ) : filteredRules.map((rule) => (
                                <tr key={rule.id} className="border-b border-end-border last:border-0 hover:bg-white/5 transition-colors">
                                    <td className="p-4">
                                        <div className="text-sm font-bold text-white">{rule.name}</div>
                                        <div className="text-[10px] text-end-text-sec italic max-w-xs truncate">{rule.description}</div>
                                    </td>
                                    <td className="p-4">
                                        <div className="text-sm text-white font-mono flex items-center gap-2">
                                            {rule.ncm && <span className="bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded text-[10px]">NCM: {rule.ncm}</span>}
                                            {rule.cfop && <span className="bg-purple-500/10 text-purple-400 px-1.5 py-0.5 rounded text-[10px]">CFOP: {rule.cfop}</span>}
                                            {!rule.ncm && !rule.cfop && <span className="text-end-text-sec text-[10px]">Alvo Geral</span>}
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={cn(
                                            "text-[10px] font-black uppercase px-2 py-0.5 rounded",
                                            rule.rule_type === 'cbs' ? "bg-orange-500/20 text-orange-400" :
                                                rule.rule_type === 'ibs' ? "bg-teal-500/20 text-teal-400" :
                                                    rule.rule_type === 'icms' ? "bg-blue-500/20 text-blue-400" :
                                                        rule.rule_type === 'pis' ? "bg-purple-500/20 text-purple-400" :
                                                            rule.rule_type === 'cofins' ? "bg-pink-500/20 text-pink-400" :
                                                                "bg-white/10 text-white"
                                        )}>
                                            {rule.rule_type}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        {rule.uf ? (
                                            <span className="bg-yellow-500/10 text-yellow-400 text-[10px] font-black px-2 py-0.5 rounded border border-yellow-500/20">
                                                {rule.uf}
                                            </span>
                                        ) : (
                                            <span className="text-[10px] text-end-text-sec italic">Nacional</span>
                                        )}
                                    </td>
                                    <td className="p-4">
                                        <div className="text-sm font-black text-end-accent">
                                            {(rule.expected_rate * 100).toFixed(2)}%
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={cn(
                                            "flex items-center gap-1 text-[10px] font-bold",
                                            rule.active ? "text-end-success" : "text-end-error"
                                        )}>
                                            <div className={cn("w-1.5 h-1.5 rounded-full", rule.active ? "bg-end-success shadow-[0_0_8px_rgba(34,197,94,0.5)]" : "bg-end-error")} />
                                            {rule.active ? "Vigente" : "Inativa"}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        <button className="p-2 text-end-text-sec hover:text-end-accent transition-colors">
                                            <Edit2 size={16} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-end-accent/5 border border-end-accent/20 rounded-lg p-6 flex gap-4">
                    <AlertCircle className="text-end-accent shrink-0" size={24} />
                    <div>
                        <h4 className="text-sm font-black text-end-accent uppercase mb-1">Nota Técnica</h4>
                        <p className="text-xs text-end-text-sec leading-relaxed">
                            A sincronização atualiza as regras globais de transição da Reforma 2026. Regras criadas manualmente ou marcadas como exceções pelo Super Admin têm prioridade sobre as tabelas federais genéricas.
                        </p>
                    </div>
                </div>
                <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-6 flex gap-4">
                    <ShieldCheck className="text-blue-400 shrink-0" size={24} />
                    <div>
                        <h4 className="text-sm font-black text-blue-400 uppercase mb-1">Integridade de Cache</h4>
                        <p className="text-xs text-end-text-sec leading-relaxed">
                            Ao salvar alterações ou sincronizar, o motor de regras da API invalidará o cache automaticamente. O próximo processamento de nota usará os dados recém-sincronizados.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

