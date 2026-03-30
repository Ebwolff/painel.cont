import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, Play, RefreshCw, Info, CheckCircle2, Search, X } from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../lib/utils';

const UFS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

interface NFeItem {
    n_item: number;
    ncm: string;
    cfop: string;
    cst: string;
    v_prod: number;
    v_icms?: number;
    v_ipi?: number;
    v_pis?: number;
    v_cofins?: number;
    v_cbs?: number;
    v_ibs?: number;
    vbc_icms?: number;
    vbc_ipi?: number;
    vbc_pis?: number;
    vbc_cofins?: number;
    vbc_cbs?: number;
    vbc_ibs?: number;
}

export function SimuladorNFe() {
    const [emitenteUf, setEmitenteUf] = useState('SP');
    const [destinatarioUf, setDestinatarioUf] = useState('SP');
    const [itens, setItens] = useState<NFeItem[]>([
        { n_item: 1, ncm: '61091000', cfop: '5102', cst: '00', v_prod: 100.00, v_icms: 0, v_ipi: 0, v_pis: 0, v_cofins: 0, v_cbs: 0, v_ibs: 0, vbc_icms: 0, vbc_ipi: 0, vbc_pis: 0, vbc_cofins: 0, vbc_cbs: 0, vbc_ibs: 0 }
    ]);
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [autoFilling, setAutoFilling] = useState(false);

    // Auto-update CFOP based on UF changes
    useEffect(() => {
        const defaultCfop = emitenteUf === destinatarioUf ? '5102' : '6102';
        setItens(prevItens => prevItens.map(item => {
            if (!item.cfop || item.cfop === '5102' || item.cfop === '6102') {
                return { ...item, cfop: defaultCfop };
            }
            if (item.cfop.length >= 4) {
                const prefix = emitenteUf === destinatarioUf ? '5' : '6';
                const firstDigit = item.cfop.charAt(0);
                const rest = item.cfop.substring(1);
                if ((prefix === '5' && firstDigit === '6') || (prefix === '6' && firstDigit === '5')) {
                    return { ...item, cfop: `${prefix}${rest}` };
                }
            }
            return item;
        }));
    }, [emitenteUf, destinatarioUf]);

    // NCM Search Modal State
    const [isNcmModalOpen, setIsNcmModalOpen] = useState(false);
    const [ncmSearchQuery, setNcmSearchQuery] = useState('');
    const [ncmSearchResults, setNcmSearchResults] = useState<any[]>([]);
    const [isSearchingNcm, setIsSearchingNcm] = useState(false);
    const [activeNcmItemIndex, setActiveNcmItemIndex] = useState<number | null>(null);

    const handleSearchNcm = async () => {
        if (!ncmSearchQuery || ncmSearchQuery.length < 3) return;
        setIsSearchingNcm(true);
        try {
            const res = await fetch(`https://brasilapi.com.br/api/ncm/v1?search=${encodeURIComponent(ncmSearchQuery)}`);
            if (res.ok) {
                const data = await res.json();
                setNcmSearchResults(data.slice(0, 10)); // Limit to top 10 results
            } else {
                setNcmSearchResults([]);
            }
        } catch (error) {
            console.error("Failed to search NCM", error);
            setNcmSearchResults([]);
        } finally {
            setIsSearchingNcm(false);
        }
    };

    const handleSelectNcm = (ncmCodigo: string) => {
        if (activeNcmItemIndex !== null) {
            handleUpdateItem(activeNcmItemIndex, 'ncm', ncmCodigo);
        }
        setIsNcmModalOpen(false);
        setNcmSearchQuery('');
        setNcmSearchResults([]);
    };

    const handleAddItem = () => {
        const defaultCfop = emitenteUf === destinatarioUf ? '5102' : '6102';
        setItens([
            ...itens,
            { n_item: itens.length + 1, ncm: '', cfop: defaultCfop, cst: '', v_prod: 0, v_icms: 0, v_ipi: 0, v_pis: 0, v_cofins: 0, v_cbs: 0, v_ibs: 0, vbc_icms: 0, vbc_ipi: 0, vbc_pis: 0, vbc_cofins: 0, vbc_cbs: 0, vbc_ibs: 0 }
        ]);
    };

    const handleUpdateItem = (index: number, field: keyof NFeItem, value: any) => {
        const newItens = [...itens];
        newItens[index] = { ...newItens[index], [field]: value };
        setItens(newItens);
    };

    const handleRemoveItem = (index: number) => {
        setItens(itens.filter((_, i) => i !== index));
    };

    const handleSimulate = async () => {
        setLoading(true);
        try {
            const response = await api.post('/simulation/validate-nfe', {
                emitente_uf: emitenteUf,
                destinatario_uf: destinatarioUf,
                itens: itens
            });
            setResult(response.data || response); // Support axios config
        } catch (error) {
            console.error("Simulation failed", error);
        } finally {
            setLoading(false);
        }
    };

    const handleAutoFillAll = async () => {
        setAutoFilling(true);
        try {
            const response = await api.post('/simulation/auto-fill-taxes', {
                emitente_uf: emitenteUf,
                destinatario_uf: destinatarioUf,
                itens: itens
            });
            const itemsTaxes = response.data?.items_taxes || response.items_taxes;

            const newItens = itens.map((item) => {
                const taxes = itemsTaxes?.find((t: any) => t.n_item === item.n_item)?.tax_values || {};
                return {
                    ...item,
                    v_icms: taxes.icms || 0,
                    v_ipi: taxes.ipi || 0,
                    v_pis: taxes.pis || 0,
                    v_cofins: taxes.cofins || 0,
                    v_cbs: taxes.cbs || 0,
                    v_ibs: taxes.ibs || 0,
                    vbc_icms: taxes.vbc_icms || 0,
                    vbc_ipi: taxes.vbc_ipi || 0,
                    vbc_pis: taxes.vbc_pis || 0,
                    vbc_cofins: taxes.vbc_cofins || 0,
                    vbc_cbs: taxes.vbc_cbs || 0,
                    vbc_ibs: taxes.vbc_ibs || 0
                };
            });
            setItens(newItens);
        } catch (error) {
            console.error("Auto-fill failed", error);
        } finally {
            setAutoFilling(false);
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-12">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 tracking-tighter italic uppercase">Simulador de NFe Compliance</h1>
                    <p className="text-end-text-sec">Valide a conformidade tributária da nota antes da emissão oficial.</p>
                </div>
                <button
                    onClick={handleSimulate}
                    disabled={loading}
                    className="bg-end-accent text-black px-8 py-3 rounded-lg font-black flex items-center gap-2 hover:scale-105 transition-all disabled:opacity-50"
                >
                    {loading ? <RefreshCw className="animate-spin" size={20} /> : <Play size={20} />}
                    EXECUTAR SIMULAÇÃO
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Inputs Section */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-end-card border border-end-border rounded-xl p-6">
                        <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                            <Info size={20} className="text-end-accent" /> Dados da Operação
                        </h3>
                        <div className="grid grid-cols-2 gap-4 mb-8">
                            <div>
                                <label className="block text-[10px] font-bold text-end-text-sec uppercase mb-1">UF Origem (Emitente)</label>
                                <select
                                    value={emitenteUf}
                                    onChange={(e) => setEmitenteUf(e.target.value)}
                                    className="w-full bg-white/5 border border-end-border rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-1 focus:ring-end-accent cursor-pointer"
                                >
                                    {UFS.map(uf => <option key={uf} value={uf} className="bg-end-card text-white">{uf}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-[10px] font-bold text-end-text-sec uppercase mb-1">UF Destino (Destinatário)</label>
                                <select
                                    value={destinatarioUf}
                                    onChange={(e) => setDestinatarioUf(e.target.value)}
                                    className="w-full bg-white/5 border border-end-border rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-1 focus:ring-end-accent cursor-pointer"
                                >
                                    {UFS.map(uf => <option key={uf} value={uf} className="bg-end-card text-white">{uf}</option>)}
                                </select>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center px-2">
                                <h3 className="text-[10px] font-black text-end-text-sec uppercase tracking-widest">Itens da Nota</h3>
                                <div className="flex gap-4">
                                    <button onClick={handleAutoFillAll} disabled={autoFilling} className="text-end-accent text-[10px] font-bold hover:underline disabled:opacity-50 flex items-center gap-1">
                                        {autoFilling ? <RefreshCw className="animate-spin" size={12} /> : '🪄'} AUTO-PREENCHER TRIBUTOS
                                    </button>
                                    <button onClick={handleAddItem} className="text-white text-[10px] font-bold hover:underline">+ ADICIONAR ITEM</button>
                                </div>
                            </div>

                            {itens.map((item, index) => (
                                <div key={index} className="flex flex-col gap-3 bg-white/[0.02] border border-white/5 p-4 rounded-lg">
                                    <div className="grid grid-cols-12 gap-2 items-end">
                                        <div className="col-span-1">
                                            <p className="text-[10px] text-end-text-sec mb-1">#</p>
                                            <p className="text-sm font-bold text-white">{item.n_item}</p>
                                        </div>
                                        <div className="col-span-3">
                                            <div className="flex items-center gap-1">
                                                <label className="block text-[9px] text-end-text-sec uppercase mb-1">NCM</label>
                                            </div>
                                            <div className="relative">
                                                <input
                                                    type="text"
                                                    value={item.ncm}
                                                    onChange={(e) => handleUpdateItem(index, 'ncm', e.target.value)}
                                                    className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 pr-8 text-xs text-white"
                                                />
                                                <button
                                                    onClick={() => { setActiveNcmItemIndex(index); setIsNcmModalOpen(true); }}
                                                    className="absolute right-2 top-1/2 -translate-y-1/2 text-end-text-sec hover:text-end-accent"
                                                    title="Buscar NCM"
                                                >
                                                    <Search size={14} />
                                                </button>
                                            </div>
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[9px] text-end-text-sec uppercase mb-1">CFOP</label>
                                            <input
                                                type="text"
                                                value={item.cfop}
                                                onChange={(e) => handleUpdateItem(index, 'cfop', e.target.value)}
                                                className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white"
                                            />
                                        </div>
                                        <div className="col-span-1">
                                            <label className="block text-[9px] text-end-text-sec uppercase mb-1">CST</label>
                                            <input
                                                type="text"
                                                value={item.cst}
                                                onChange={(e) => handleUpdateItem(index, 'cst', e.target.value)}
                                                className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white"
                                            />
                                        </div>
                                        <div className="col-span-3">
                                            <label className="block text-[9px] text-end-text-sec uppercase mb-1">Valor Prod.</label>
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={item.v_prod}
                                                onChange={(e) => handleUpdateItem(index, 'v_prod', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white font-mono"
                                            />
                                        </div>
                                        <div className="col-span-2 flex justify-end">
                                            <button onClick={() => handleRemoveItem(index)} className="text-end-error text-[10px] font-bold hover:underline mb-1">REMOVER</button>
                                        </div>
                                    </div>

                                    {/* Bases de Cálculo */}
                                    <div className="grid grid-cols-12 gap-2 items-end border-t border-white/5 pt-3 mt-1">
                                        <div className="col-span-12">
                                            <p className="text-[9px] font-bold text-end-accent uppercase mb-1 opacity-80">Bases de Cálculo - vBC (R$)</p>
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">ICMS</label>
                                            <input type="number" step="0.01" value={item.vbc_icms ?? 0} onChange={(e) => handleUpdateItem(index, 'vbc_icms', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white font-mono" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">IPI</label>
                                            <input type="number" step="0.01" value={item.vbc_ipi ?? 0} onChange={(e) => handleUpdateItem(index, 'vbc_ipi', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white font-mono" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">PIS</label>
                                            <input type="number" step="0.01" value={item.vbc_pis ?? 0} onChange={(e) => handleUpdateItem(index, 'vbc_pis', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white font-mono" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">COFINS</label>
                                            <input type="number" step="0.01" value={item.vbc_cofins ?? 0} onChange={(e) => handleUpdateItem(index, 'vbc_cofins', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white font-mono" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">CBS</label>
                                            <input type="number" step="0.01" value={item.vbc_cbs ?? 0} onChange={(e) => handleUpdateItem(index, 'vbc_cbs', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white font-mono" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">IBS</label>
                                            <input type="number" step="0.01" value={item.vbc_ibs ?? 0} onChange={(e) => handleUpdateItem(index, 'vbc_ibs', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-white font-mono" />
                                        </div>
                                    </div>

                                    {/* Valores dos Impostos */}
                                    <div className="grid grid-cols-12 gap-2 items-end border-t border-white/5 pt-3 mt-2 mb-2">
                                        <div className="col-span-12">
                                            <p className="text-[9px] font-bold text-end-accent uppercase mb-1 opacity-80">Valor do Imposto Destacado (R$)</p>
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">ICMS</label>
                                            <input type="number" step="0.01" value={item.v_icms ?? 0} onChange={(e) => handleUpdateItem(index, 'v_icms', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-end-accent font-mono font-bold" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">IPI</label>
                                            <input type="number" step="0.01" value={item.v_ipi ?? 0} onChange={(e) => handleUpdateItem(index, 'v_ipi', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-end-accent font-mono font-bold" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">PIS</label>
                                            <input type="number" step="0.01" value={item.v_pis ?? 0} onChange={(e) => handleUpdateItem(index, 'v_pis', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-end-accent font-mono font-bold" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">COFINS</label>
                                            <input type="number" step="0.01" value={item.v_cofins ?? 0} onChange={(e) => handleUpdateItem(index, 'v_cofins', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-end-accent font-mono font-bold" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">CBS</label>
                                            <input type="number" step="0.01" value={item.v_cbs ?? 0} onChange={(e) => handleUpdateItem(index, 'v_cbs', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-end-accent font-mono font-bold" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-[8px] text-end-text-sec uppercase mb-1">IBS</label>
                                            <input type="number" step="0.01" value={item.v_ibs ?? 0} onChange={(e) => handleUpdateItem(index, 'v_ibs', parseFloat(e.target.value) || 0)} className="w-full bg-white/5 border border-end-border rounded px-2 py-1.5 text-xs text-end-accent font-mono font-bold" />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Results Section */}
                <div className="space-y-6">
                    {!result ? (
                        <div className="bg-end-card border border-end-border rounded-xl p-12 text-center border-dashed">
                            <ShieldCheck size={48} className="text-end-border mx-auto mb-4" />
                            <p className="text-end-text-sec text-sm">Preencha os dados e execute para ver a conformidade fiscal.</p>
                        </div>
                    ) : (
                        <div className="space-y-6 animate-in slide-in-from-right duration-500">
                            {/* Score Card */}
                            <div className={cn(
                                "border rounded-xl p-6 text-center shadow-2xl",
                                result.compliance_score >= 80 ? "bg-end-success/10 border-end-success/30" : "bg-end-error/10 border-end-error/30"
                            )}>
                                <p className="text-[10px] font-bold uppercase tracking-widest mb-2 opacity-70">Compliance Score</p>
                                <h4 className={cn(
                                    "text-6xl font-black mb-2",
                                    result.compliance_score >= 80 ? "text-end-success" : "text-end-error"
                                )}>
                                    {result.compliance_score}%
                                </h4>
                                <p className="text-sm font-bold text-white uppercase tracking-tighter italic">{result.recomendacao}</p>
                            </div>

                            {/* Alertas */}
                            <div className="bg-end-card border border-end-border rounded-xl p-6">
                                <h3 className="text-[10px] font-black text-end-text-sec uppercase tracking-widest mb-6">Inconsistências Detectadas</h3>

                                {result.alertas.length === 0 ? (
                                    <div className="flex items-center gap-3 text-end-success">
                                        <CheckCircle2 size={24} />
                                        <p className="font-bold text-sm">Nenhuma divergência encontrada!</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {result.alertas.map((alerta: any, idx: number) => (
                                            <div key={idx} className="bg-white/5 border-l-4 border-end-error p-3 rounded">
                                                <p className="text-[10px] font-bold text-white mb-1 uppercase tracking-tight">{alerta.tipo.replace('_', ' ')}</p>
                                                <p className="text-xs text-end-text-sec leading-relaxed">{alerta.mensagem}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Tax Info */}
                            <div className="bg-end-card border border-end-border rounded-xl p-6">
                                <h3 className="text-[10px] font-black text-end-text-sec uppercase tracking-widest mb-6">Resumo Estimado (IBS/CBS)</h3>
                                <div className="space-y-4">
                                    <div className="flex justify-between items-end">
                                        <span className="text-[10px] text-end-text-sec uppercase font-bold tracking-tight">Total CBS</span>
                                        <span className="text-lg font-black text-white">
                                            {result.items_results.reduce((acc: number, r: any) => acc + (r.tax_values?.cbs || 0), 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-end">
                                        <span className="text-[10px] text-end-text-sec uppercase font-bold tracking-tight">Total IBS</span>
                                        <span className="text-lg font-black text-white">
                                            {result.items_results.reduce((acc: number, r: any) => acc + (r.tax_values?.ibs || 0), 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* NCM Search Modal */}
            {isNcmModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-end-card border border-end-border rounded-xl w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                        <div className="p-4 border-b border-end-border flex justify-between items-center bg-white/[0.02]">
                            <h3 className="font-bold text-white flex items-center gap-2"><Search size={18} className="text-end-accent" /> Buscar NCM por Produto</h3>
                            <button onClick={() => setIsNcmModalOpen(false)} className="text-end-text-sec hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={ncmSearchQuery}
                                    onChange={(e) => setNcmSearchQuery(e.target.value)}
                                    placeholder="Ex: Computador, Cadeira, Tomate..."
                                    onKeyDown={(e) => e.key === 'Enter' && handleSearchNcm()}
                                    className="flex-1 bg-black/50 border border-end-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-end-accent"
                                    autoFocus
                                />
                                <button
                                    onClick={handleSearchNcm}
                                    disabled={isSearchingNcm || ncmSearchQuery.length < 3}
                                    className="bg-end-accent text-black px-4 py-2 rounded-lg font-bold disabled:opacity-50 flex items-center gap-2 hover:opacity-90 transition-opacity"
                                >
                                    {isSearchingNcm ? <RefreshCw size={18} className="animate-spin" /> : 'Buscar'}
                                </button>
                            </div>

                            <div className="max-h-[60vh] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                                {ncmSearchResults.length === 0 && ncmSearchQuery && !isSearchingNcm && (
                                    <p className="text-center text-end-text-sec py-8 text-sm italic">Nenhum resultado encontrado. Tente outro termo.</p>
                                )}

                                {ncmSearchResults.map((ncm) => (
                                    <div
                                        key={ncm.codigo}
                                        onClick={() => handleSelectNcm(ncm.codigo)}
                                        className="bg-white/5 border border-white/10 p-3 rounded-lg hover:border-end-accent cursor-pointer transition-all group"
                                    >
                                        <div className="flex justify-between items-start gap-4">
                                            <div className="flex-1">
                                                <p className="text-sm text-white font-medium break-words leading-tight">{ncm.descricao}</p>
                                            </div>
                                            <span className="bg-end-accent/20 text-end-accent font-mono text-xs font-bold px-2 py-1 rounded shrink-0 group-hover:bg-end-accent group-hover:text-black transition-colors">
                                                {ncm.codigo}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
