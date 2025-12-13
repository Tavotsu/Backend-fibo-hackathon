import React from 'react';
import { MonitorPlay } from 'lucide-react';
import { GeneratedImage } from '../../../types';

interface StatusIndicatorProps {
    isProcessing: boolean;
    activeImage: GeneratedImage | undefined;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ isProcessing, activeImage }) => {
    return (
        <div className="flex items-center gap-4 text-sm text-zinc-500">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800">
                <MonitorPlay className="w-3.5 h-3.5" />
                {isProcessing ? 'Procesando Solicitud' : activeImage ? 'Visualización Activa' : 'Esperando Entrada'}
            </span>
            {activeImage && !isProcessing && (
                <span className="hidden md:inline-block max-w-[300px] truncate opacity-50">
                    "{activeImage.prompt_used}"
                </span>
            )}
        </div>
    );
};
