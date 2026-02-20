import React, { useState, useCallback, useEffect } from 'react';
import { UploadCloud, FileType, CheckCircle, XCircle, AlertTriangle, ShieldCheck, Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { api } from '../services/api';
import { useFeatures } from '../hooks/useFeatures';

export function Upload() {
    const navigate = useNavigate();
    const { hasFeature, tier } = useFeatures();
    const [activeTab, setActiveTab] = useState<'manual' | 'sefaz'>('manual');
    const [companies, setCompanies] = useState<any[]>([]);
    const [selectedCompany, setSelectedCompany] = useState<string>('');
    const [isDragging, setIsDragging] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    React.useEffect(() => {
        async function fetchCompanies() {
            try {
                const data = await api.get('/companies/');
                setCompanies(data);
                if (data.length > 0) setSelectedCompany(data[0].id);
            } catch (err) {
                console.error("Failed to fetch companies", err);
            }
        }
        fetchCompanies();
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && droppedFile.name.endsWith('.xml')) {
            setFile(droppedFile);
            setResult(null);
            setError(null);
        } else {
            setError("Apenas arquivos .xml são permitidos.");
        }
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selected = e.target.files[0];
            if (selected.name.endsWith('.xml')) {
                setFile(selected);
                setResult(null);
                setError(null);
            } else {
                setError("Apenas arquivos .xml são permitidos.");
            }
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);
        if (selectedCompany) {
            formData.append('empresa_id', selectedCompany);
        }

        try {
            const data = await api.upload('/upload/xml', formData);
            setResult(data);
        } catch (err: any) {
            setError(err.message || "Erro ao processar o arquivo. Verifique se o backend está rodando.");
            console.error(err);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Tabs */}
            <div className="flex border-b border-end-border mb-8">
                <button
                    onClick={() => setActiveTab('manual')}
                    className={cn(
                        "px-6 py-3 text-sm font-bold uppercase tracking-widest transition-all border-b-2",
                        activeTab === 'manual' ? "border-end-accent text-end-accent" : "border-transparent text-end-text-sec hover:text-white"
                    )}
                >
                    Upload Manual (XML)
                </button>
                <button
                    onClick={() => setActiveTab('sefaz')}
                    className={cn(
                        "px-6 py-3 text-sm font-bold uppercase tracking-widest transition-all border-b-2 flex items-center gap-2",
                        activeTab === 'sefaz' ? "border-end-accent text-end-accent" : "border-transparent text-end-text-sec hover:text-white"
                    )}
                >
                    Sincronização SEFAZ
                    {!hasFeature('sefaz_sync') && <Star size={12} className="text-end-accent animate-pulse" />}
                </button>
            </div>

            {activeTab === 'manual' ? (
                <>
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-white">Análise de XML</h1>
                        <div className="flex items-center gap-3">
                            <span className="text-xs font-bold text-end-text-sec uppercase">Empresa Destino:</span>
                            <select
                                value={selectedCompany}
                                onChange={e => setSelectedCompany(e.target.value)}
                                className="bg-end-card border border-end-border text-end-accent text-xs font-bold py-1.5 px-3 rounded focus:outline-none focus:border-end-accent transition-colors"
                            >
                                {companies.map(c => (
                                    <option key={c.id} value={c.id}>{c.razao_social}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Upload Zone */}
                    <div
                        className={cn(
                            "border-2 border-dashed rounded-lg p-12 flex flex-col items-center justify-center transition-colors cursor-pointer",
                            isDragging ? "border-end-accent bg-end-accent/5" : "border-end-border bg-end-card hover:bg-white/5",
                            result && "border-end-success"
                        )}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                    >
                        <input
                            type="file"
                            accept=".xml"
                            className="hidden"
                            id="file-upload"
                            onChange={handleFileChange}
                        />
                        <label htmlFor="file-upload" className="flex flex-col items-center cursor-pointer w-full">
                            <div className="h-16 w-16 bg-end-bg rounded-full flex items-center justify-center mb-4 text-end-accent">
                                <UploadCloud size={32} />
                            </div>
                            <p className="text-lg font-medium text-white">
                                {file ? file.name : "Arraste e solte o XML aqui"}
                            </p>
                            <p className="text-sm text-end-text-sec mt-2">
                                ou clique para selecionar do computador
                            </p>
                        </label>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="mt-4 p-4 bg-red-500/10 border border-end-error rounded-md flex items-center gap-3 text-end-error">
                            <AlertTriangle size={20} />
                            {error}
                        </div>
                    )}

                    {/* Upload Button */}
                    {file && !result && (
                        <div className="mt-6 flex justify-end">
                            <button
                                onClick={handleUpload}
                                disabled={uploading}
                                className="bg-end-accent hover:bg-end-accent-hover text-black font-bold py-2.5 px-6 rounded-md transition-colors disabled:opacity-50"
                            >
                                {uploading ? "Processando..." : "Analisar Conformidade"}
                            </button>
                        </div>
                    )}
                </>
            ) : (
                <div className="bg-end-card border border-end-border rounded-xl p-12 text-center space-y-6">
                    <div className="h-20 w-20 bg-end-accent/10 rounded-full flex items-center justify-center mx-auto text-end-accent">
                        <Star size={40} />
                    </div>
                    <div className="max-w-md mx-auto">
                        <h2 className="text-2xl font-black text-white uppercase tracking-tighter italic">Sincronização SEFAZ (A1)</h2>
                        <p className="text-end-text-sec mt-4">
                            Esqueça o upload manual. Com o plano **Monitor Profissional**, o END Monitor busca todas as notas emitidas contra o CNPJ dos seus clientes diretamente na SEFAZ.
                        </p>
                    </div>

                    {!hasFeature('sefaz_sync') ? (
                        <div className="pt-6">
                            <button
                                onClick={() => navigate('/planos')}
                                className="bg-end-accent text-black px-8 py-3 rounded font-black text-sm hover:scale-105 transition-transform shadow-lg shadow-end-accent/20"
                            >
                                LIBERAR AUTOMAÇÃO (PLANO PRO)
                            </button>
                            <p className="text-[10px] text-end-text-sec mt-4 uppercase font-bold tracking-widest flex items-center justify-center gap-2">
                                <ShieldCheck size={12} /> Exclusivo para assinantes PRO e Enterprise
                            </p>
                        </div>
                    ) : (
                        <div className="bg-white/5 p-6 rounded-lg text-end-accent font-bold italic">
                            Sincronização ativa! O sistema está processando notas automaticamente.
                        </div>
                    )}
                </div>
            )}

            {/* Results */}
            {result && (
                <div className="mt-8 space-y-6 animate-in slide-in-from-bottom-4 duration-500">
                    <h2 className="text-xl font-bold text-white">Resultado da Análise</h2>

                    {/* Status Card */}
                    {result.already_exists && (
                        <div className="mb-6 p-4 bg-end-accent/10 border border-end-accent/30 rounded-lg flex items-center gap-3 text-end-accent">
                            <AlertTriangle size={20} />
                            <div className="text-sm font-medium">Nota já processada anteriormente. Exibindo dados extraídos do banco de dados.</div>
                        </div>
                    )}

                    <div className={cn(
                        "p-6 rounded-lg border flex items-center gap-4",
                        result.validation.status === 'conforme'
                            ? "bg-end-success/10 border-end-success text-end-success"
                            : "bg-end-error/10 border-end-error text-end-error"
                    )}>
                        {result.validation.status === 'conforme' ? <CheckCircle size={32} /> : <XCircle size={32} />}
                        <div>
                            <div className="text-lg font-bold uppercase">
                                {result.validation.status === 'conforme' ? "Conformidade Total" : "Divergência Encontrada"}
                            </div>
                            <p className="text-sm opacity-80">
                                {result.validation.status === 'conforme'
                                    ? "Os tributos foram validados de acordo com as regras fiscais vigentes."
                                    : "Foram identificados erros de cálculo ou alíquotas incorretas nos tributos analisados."}
                            </p>
                        </div>
                    </div>

                    {/* Details Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-end-card border border-end-border p-5 rounded-lg">
                            <h3 className="text-sm font-medium text-end-text-sec mb-4 uppercase tracking-wider">Dados da Nota</h3>
                            <div className="space-y-3">
                                <div className="flex justify-between border-b border-end-border pb-2">
                                    <span className="text-end-text-sec">Número</span>
                                    <span className="text-white font-mono">{result.parsed_data.numero}</span>
                                </div>
                                <div className="flex justify-between border-b border-end-border pb-2">
                                    <span className="text-end-text-sec">Emitente</span>
                                    <span className="text-white">{result.parsed_data.emitente_nome?.substring(0, 20)}...</span>
                                </div>
                                <div className="flex justify-between border-b border-end-border pb-2">
                                    <span className="text-end-text-sec">Valor Total</span>
                                    <span className="text-white font-mono font-bold">R$ {result.parsed_data.valor_total.toFixed(2)}</span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-end-card border border-end-border p-5 rounded-lg">
                            <h3 className="text-sm font-medium text-end-text-sec mb-4 uppercase tracking-wider">Validação Tributária</h3>
                            <div className="space-y-3">
                                <div className="flex justify-between items-center border-b border-end-border pb-2">
                                    <span className="text-end-text-sec">CBS (0.9%)</span>
                                    <div className="text-right">
                                        <div className={cn("font-mono font-bold", result.validation.validation_details.cbs_ok ? "text-end-success" : "text-end-error")}>
                                            {result.parsed_data.valor_cbs.toFixed(2)}
                                        </div>
                                        <div className="text-xs text-end-text-sec">Esperado: {result.validation.validation_details.cbs_esperado.toFixed(2)}</div>
                                    </div>
                                </div>
                                <div className="flex justify-between items-center border-b border-end-border pb-2">
                                    <span className="text-end-text-sec">IBS (0.1%)</span>
                                    <div className="text-right">
                                        <div className={cn("font-mono font-bold", result.validation.validation_details.ibs_ok ? "text-end-success" : "text-end-error")}>
                                            {result.parsed_data.valor_ibs.toFixed(2)}
                                        </div>
                                        <div className="text-xs text-end-text-sec">Esperado: {result.validation.validation_details.ibs_esperado.toFixed(2)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
