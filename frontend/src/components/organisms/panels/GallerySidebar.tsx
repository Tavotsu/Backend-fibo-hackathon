import React from 'react';
import { PanelRightClose, PanelRightOpen } from 'lucide-react';
import { GeneratedImage } from '../../../types';

interface GallerySidebarProps {
    isOpen: boolean;
    setIsOpen: (v: boolean) => void;
    images: GeneratedImage[];
    activeImageId: string | null;
    setActiveImageId: (id: string) => void;
    isProcessing: boolean;
}

export const GallerySidebar: React.FC<GallerySidebarProps> = ({
    isOpen, setIsOpen,
    images, activeImageId, setActiveImageId,
    isProcessing
}) => {
    return (
        <aside
            className={`${isOpen ? 'w-24 md:w-32' : 'w-0'} transition-all duration-300 ease-in-out border-l border-zinc-800 bg-zinc-900/80 backdrop-blur-sm flex flex-col z-20 relative`}
        >
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="absolute -left-8 top-4 bg-zinc-900 border border-r-0 border-zinc-800 p-1.5 rounded-l-md text-zinc-400 hover:text-white z-50 transition-colors"
                title={isOpen ? "Ocultar galería" : "Mostrar galería"}
            >
                {isOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
            </button>

            <div className={`${isOpen ? 'opacity-100 visible' : 'opacity-0 invisible w-0'} transition-all duration-200 flex flex-col h-full overflow-hidden`}>
                <div className="p-4 border-b border-zinc-800">
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest block text-center">
                        Galería
                    </span>
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
                    {images.map((img) => (
                        <button
                            key={img.id}
                            onClick={() => setActiveImageId(img.id)}
                            disabled={isProcessing}
                            className={`w-full aspect-square rounded-md overflow-hidden border-2 transition-all relative group
            ${activeImageId === img.id
                                    ? 'border-primary shadow-[0_0_15px_rgba(var(--primary),0.3)] ring-1 ring-primary'
                                    : 'border-zinc-800 opacity-60 hover:opacity-100 hover:border-zinc-600'}
            ${isProcessing ? 'opacity-40 grayscale' : ''}
          `}
                        >
                            <img
                                src={img.url}
                                alt="Thumbnail"
                                className="w-full h-full object-cover"
                            />
                            {activeImageId === img.id && (
                                <div className="absolute inset-0 bg-primary/10" />
                            )}
                        </button>
                    ))}

                    {images.length === 0 && !isProcessing && (
                        <div className="text-[10px] text-zinc-600 text-center mt-10 px-2">
                            Sin Imágenes
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
};
