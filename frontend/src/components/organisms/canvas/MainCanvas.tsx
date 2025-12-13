import React, { useEffect, useRef } from 'react';
import { Download, Maximize2, Loader2, Terminal } from 'lucide-react';
import { Button } from '../../atoms/actions/Button';
import { StatusIndicator } from '../../molecules/feedback/StatusIndicator';
import { GeneratedImage, JobStatusResponse } from '../../../types';

interface MainCanvasProps {
    isProcessing: boolean;
    jobStatus: JobStatusResponse | null;
    activeImage: GeneratedImage | undefined;
}

export const MainCanvas: React.FC<MainCanvasProps> = ({ isProcessing, jobStatus, activeImage }) => {
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll logs
    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [jobStatus?.events]);

    return (
        <main className="flex-1 flex flex-col h-full relative bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-zinc-900 via-zinc-950 to-zinc-950">

            {/* Top Toolbar */}
            <div className="h-16 border-b border-zinc-800/50 flex items-center justify-between px-6 bg-zinc-950/50 backdrop-blur-sm absolute top-0 w-full z-10 transition-colors">
                <StatusIndicator isProcessing={isProcessing} activeImage={activeImage} />

                {activeImage && !isProcessing && (
                    <Button variant="outline" size="sm" className="gap-2 h-8 border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300">
                        <Download className="w-3.5 h-3.5" /> Exportar HD
                    </Button>
                )}
            </div>

            {/* Canvas Center */}
            <div className="flex-1 flex items-center justify-center p-8 overflow-hidden relative">

                {isProcessing ? (
                    /* LOADING SCREEN OVERLAY */
                    <div className="w-full max-w-lg p-8 rounded-xl bg-white/80 dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 backdrop-blur-xl shadow-2xl flex flex-col gap-6 animate-in fade-in zoom-in-95 duration-500">

                        <div className="flex flex-col items-center justify-center space-y-4">
                            <div className="relative">
                                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse" />
                                <Loader2 className="w-12 h-12 text-primary animate-spin relative z-10" />
                            </div>
                            <div className="text-center">
                                <h3 className="text-lg font-semibold text-zinc-900 dark:text-white tracking-tight">Generando Assets</h3>
                                <p className="text-sm text-zinc-500 dark:text-zinc-400">El modelo está interpretando tu prompt...</p>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between text-xs uppercase tracking-wider font-bold text-zinc-500">
                                <span>Progreso del Job</span>
                                <span>{jobStatus ? Math.round(jobStatus.progress) : 0}%</span>
                            </div>
                            <div className="h-2 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-blue-600 to-primary transition-all duration-300 ease-out"
                                    style={{ width: `${jobStatus ? jobStatus.progress : 0}%` }}
                                />
                            </div>
                        </div>

                        <div className="bg-stone-50/50 dark:bg-black/50 rounded-md border border-zinc-200 dark:border-zinc-800/50 p-4 font-mono text-xs text-zinc-500 dark:text-zinc-400 h-48 flex flex-col">
                            <div className="flex items-center gap-2 border-b border-zinc-200 dark:border-zinc-800/50 pb-2 mb-2 text-zinc-500">
                                <Terminal className="w-3 h-3" />
                                <span>System Logs</span>
                            </div>
                            <div className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-2">
                                {jobStatus?.events?.map((event: any, i: number) => {
                                    // Fix for React Error #31: Handle object events {t, msg} vs strings
                                    const message = typeof event === 'object' && event !== null && event.msg
                                        ? event.msg
                                        : typeof event === 'string'
                                            ? event
                                            : JSON.stringify(event);

                                    return (
                                        <div key={i} className="flex gap-2 animate-in slide-in-from-left-2 duration-300">
                                            <span className="text-zinc-600 shrink-0">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                                            <span className={i === ((jobStatus?.events?.length || 0) - 1) ? "text-primary font-semibold" : "text-zinc-400"}>
                                                {message}
                                            </span>
                                        </div>
                                    );
                                })}
                                {(!jobStatus || !jobStatus.events || jobStatus.events.length === 0) && (
                                    <span className="text-zinc-400 dark:text-zinc-700 italic">Esperando conexión al servidor...</span>
                                )}
                                <div ref={logsEndRef} />
                            </div>
                        </div>

                    </div>
                ) : activeImage ? (
                    <div className="relative group max-w-full max-h-full flex flex-col items-center">
                        <div className="relative shadow-2xl shadow-black/20 dark:shadow-black rounded-lg overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-3xl">
                            <img
                                src={activeImage.url}
                                alt="Generated content"
                                className="max-h-[calc(100vh-140px)] max-w-full object-contain animate-in fade-in zoom-in-95 duration-500"
                            />
                            <div className="absolute inset-0 ring-1 ring-black/5 dark:ring-white/10 pointer-events-none rounded-lg" />
                        </div>
                    </div>
                ) : (
                    <div className="text-center space-y-4 opacity-30 select-none">
                        <div className="w-32 h-32 mx-auto rounded-full border-4 border-dashed border-zinc-300 dark:border-zinc-700 flex items-center justify-center">
                            <Maximize2 className="w-12 h-12 text-zinc-400 dark:text-zinc-700" />
                        </div>
                        <p className="text-xl font-medium text-zinc-400 dark:text-zinc-500">El canvas está vacío</p>
                        <p className="text-sm text-zinc-500 dark:text-zinc-600">Configura los parámetros a la izquierda para comenzar</p>
                    </div>
                )}
            </div>

        </main>
    );
};
