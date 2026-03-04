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
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
    const [results, setResults] = useState<any[]>([]);
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
        const droppedFiles = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.xml'));
        if (droppedFiles.length > 0) {
            setFiles(prev => [...prev, ...droppedFiles]);
            setResults([]);
            setError(null);
        } else {
            setError("Apenas arquivos .xml são permitidos.");
        }
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const selectedFiles = Array.from(e.target.files).filter(f => f.name.endsWith('.xml'));
            if (selectedFiles.length > 0) {
                setFiles(prev => [...prev, ...selectedFiles]);
                setResults([]);
                setError(null);
            } else {
                setError("Apenas arquivos .xml são permitidos.");
            }
        }
    };

    const handleUpload = async () => {
        if (files.length === 0) return;

        setUploading(true);
        setError(null);
        setUploadProgress({ current: 0, total: files.length });
        setResults([]);

        const BATCH_SIZE = 3; // Lote de envios paralelos para não sobrecarregar
        let processedCount = 0;
        const newResults: any[] = [];

        for (let i = 0; i < files.length; i += BATCH_SIZE) {
            const batch = files.slice(i, i + BATCH_SIZE);
            const batchPromises = batch.map(async (f) => {
                const formData = new FormData();
                formData.append('file', f);
                if (selectedCompany) {
                    formData.append('empresa_id', selectedCompany);
                }

                try {
                    const data = await api.upload('/upload/xml', formData);
                    return {
                        file: f.name,
                        success: true,
                        data: data
                    };
                } catch (err: any) {
                    return {
                        file: f.name,
                        success: false,
                        error: err.message || "Erro no processamento"
                    };
                }
            });

            const batchResults = await Promise.all(batchPromises);
            newResults.push(...batchResults);

            processedCount += batch.length;
            setUploadProgress({ current: processedCount, total: files.length });
        }

        setResults(newResults);
        setUploading(false);
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
                            results.length > 0 && "border-end-success"
                        )}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                    >
                        <input
                            type="file"
                            accept=".xml"
                            multiple
                            className="hidden"
                            id="file-upload"
                            onChange={handleFileChange}
                        />
                        <label htmlFor="file-upload" className="flex flex-col items-center cursor-pointer w-full">
                            <div className="h-16 w-16 bg-end-bg rounded-full flex items-center justify-center mb-4 text-end-accent">
                                <UploadCloud size={32} />
                            </div>
                            <p className="text-lg font-medium text-white">
                                {files.length > 0 ? `${files.length} arquivo(s) selecionado(s)` : "Arraste e solte o(s) XML(s) aqui"}
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

                    {/* Upload Button & Progress */}
                    {files.length > 0 && results.length === 0 && !uploading && (
                        <div className="mt-6 flex justify-between items-center">
                            <button
                                onClick={() => setFiles([])}
                                className="text-end-text-sec hover:text-white transition-colors text-sm font-bold uppercase tracking-widest"
                            >
                                Limpar
                            </button>
                            <button
                                onClick={handleUpload}
                                disabled={uploading}
                                className="bg-end-accent hover:bg-end-accent-hover text-black font-bold py-2.5 px-6 rounded-md transition-colors disabled:opacity-50"
                            >
                                Iniciar Processamento ({files.length} notas)
                            </button>
                        </div>
                    )}

                    {/* Progress Bar */}
                    {uploading && (
                        <div className="mt-6 space-y-2 animate-in slide-in-from-bottom-2">
                            <div className="flex justify-between text-sm font-bold">
                                <span className="text-end-accent">Enviando notas para a fila de auditoria...</span>
                                <span className="text-white">{uploadProgress.current} / {uploadProgress.total}</span>
                            </div>
                            <div className="h-2 bg-end-bg rounded-full overflow-hidden border border-end-border">
                                <div
                                    className="h-full bg-end-accent transition-all duration-300"
                                    style={{ width: `${uploadProgress.total > 0 ? (uploadProgress.current / uploadProgress.total) * 100 : 0}%` }}
                                ></div>
                            </div>
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

            {/* Results Table */}
            {results.length > 0 && (
                <div className="mt-8 space-y-6 animate-in slide-in-from-bottom-4 duration-500">
                    <div className="flex justify-between items-center">
                        <h2 className="text-xl font-bold text-white">Resultados do Envio ({results.length})</h2>
                        <button
                            onClick={() => { setFiles([]); setResults([]); setError(null); }}
                            className="bg-end-bg hover:bg-white/5 border border-end-border text-white font-bold py-2 px-4 rounded-md transition-colors text-sm"
                        >
                            Novo Lote
                        </button>
                    </div>

                    <div className="bg-end-card border border-end-border rounded-lg overflow-hidden">
                        <table className="w-full text-left text-sm text-end-text-sec">
                            <thead className="text-xs uppercase bg-black/20 text-end-text">
                                <tr>
                                    <th className="px-6 py-4 font-bold tracking-widest">Arquivo</th>
                                    <th className="px-6 py-4 font-bold tracking-widest text-center">Status</th>
                                    <th className="px-6 py-4 font-bold tracking-widest">Detalhes</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-end-border">
                                {results.map((res, index) => (
                                    <tr key={index} className="hover:bg-white/[0.02] transition-colors">
                                        <td className="px-6 py-4 font-medium text-white font-mono break-all max-w-[200px] truncate">
                                            {res.file}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {res.success ? (
                                                res.data.status === 'already_processed' || res.data.already_exists ? (
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-end-accent/10 border border-end-accent/30 text-end-accent text-xs font-bold uppercase tracking-widest">
                                                        <AlertTriangle size={12} /> Duplicada
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-end-success/10 border border-end-success/30 text-end-success text-xs font-bold uppercase tracking-widest">
                                                        <CheckCircle size={12} /> Na Fila
                                                    </span>
                                                )
                                            ) : (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-end-error/10 border border-end-error/30 text-end-error text-xs font-bold uppercase tracking-widest">
                                                    <XCircle size={12} /> Erro
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-xs opacity-80">
                                            {res.success ?
                                                res.data.message :
                                                res.error}
                                            {res.data && res.data.job_id && (
                                                <div className="text-[10px] font-mono mt-1 opacity-50 text-end-text-sec">JOB ID: {res.data.job_id}</div>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
