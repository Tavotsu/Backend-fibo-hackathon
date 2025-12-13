import React from 'react';
import { PanelLeftClose, PanelLeftOpen, Cpu, Layers, Send, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '../../atoms/actions/Button';
import { Textarea } from '../../atoms/inputs/Textarea';
import { ImageUploader } from '../../molecules/selectors/ImageUploader';
import { ThemeToggle } from '../../molecules/toggles/ThemeToggle';
import { CameraAngleSelector } from '../../molecules/selectors/CameraAngleSelector';
import { QuantitySelector } from '../../molecules/selectors/QuantitySelector';

interface SidebarControlsProps {
    isOpen: boolean;
    setIsOpen: (v: boolean) => void;
    isDarkMode: boolean;
    setIsDarkMode: (v: boolean) => void;

    selectedImage: string | null;
    setSelectedImage: (s: string | null) => void;

    prompt: string;
    setPrompt: (s: string) => void;

    selectedAngle: string;
    setSelectedAngle: (s: string) => void;

    quantity: number;
    setQuantity: (n: number) => void;

    isProcessing: boolean;
    error: string | null;
    onSubmit: () => void;
}

export const SidebarControls: React.FC<SidebarControlsProps> = ({
    isOpen, setIsOpen,
    isDarkMode, setIsDarkMode,
    selectedImage, setSelectedImage,
    prompt, setPrompt,
    selectedAngle, setSelectedAngle,
    quantity, setQuantity,
    isProcessing, error, onSubmit
}) => {
    return (
        <aside
            className={`${isOpen ? 'w-80 md:w-96' : 'w-0'} transition-all duration-300 ease-in-out flex flex-col border-r border-zinc-800 dark:border-zinc-800 bg-zinc-900/50 dark:bg-zinc-900/50 backdrop-blur-sm z-20 relative`}
        >
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="absolute -right-8 top-4 bg-zinc-900 border border-l-0 border-zinc-800 p-1.5 rounded-r-md text-zinc-400 hover:text-white z-50 transition-colors"
                title={isOpen ? "Ocultar panel" : "Mostrar panel"}
            >
                {isOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
            </button>

            <div className={`${isOpen ? 'opacity-100 visible' : 'opacity-0 invisible w-0'} transition-all duration-200 flex flex-col h-full overflow-hidden`}>

                {/* Header */}
                <div className="p-5 border-b border-zinc-800 dark:border-zinc-800 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-primary rounded-md">
                            <Cpu className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="font-bold text-lg leading-none tracking-tight">Marketech</h1>
                            <p className="text-[10px] text-zinc-400 font-medium tracking-wide">Modelo 0.1a</p>
                        </div>
                    </div>

                    <ThemeToggle isDarkMode={isDarkMode} toggle={() => setIsDarkMode(!isDarkMode)} />
                </div>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto p-5 space-y-8 custom-scrollbar">

                    {/* Reference Image */}
                    <div className="space-y-3">
                        <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                            <Layers className="w-3 h-3" /> Input Source
                        </label>
                        <ImageUploader
                            onImageSelected={setSelectedImage}
                            selectedImage={selectedImage}
                        />
                    </div>

                    {/* Prompt */}
                    <div className="space-y-3">
                        <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                            Creative Prompt
                        </label>
                        <Textarea
                            placeholder="Describe tu visión para la imagen de marketing..."
                            className="min-h-[100px] resize-none bg-zinc-950/50 border-zinc-800 focus:border-primary/50 transition-colors placeholder:text-zinc-400 dark:placeholder:text-zinc-600"
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            disabled={isProcessing}
                        />
                    </div>

                    {/* Camera Angles */}
                    <CameraAngleSelector
                        selectedAngle={selectedAngle}
                        setSelectedAngle={setSelectedAngle}
                        isProcessing={isProcessing}
                    />

                    {/* Quantity */}
                    <QuantitySelector
                        quantity={quantity}
                        setQuantity={setQuantity}
                        isProcessing={isProcessing}
                    />

                    {/* Error Display */}
                    {error && (
                        <div className="mt-4 p-3 bg-red-900/20 border border-red-900/50 rounded-md text-red-200 text-xs flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                            <div>{error}</div>
                        </div>
                    )}

                </div>

                {/* Footer Actions */}
                <div className="p-5 border-t border-zinc-800 dark:border-zinc-800 bg-zinc-900/80 dark:bg-zinc-900/80">
                    <Button
                        onClick={onSubmit}
                        disabled={isProcessing || (!prompt && !selectedImage)}
                        className="w-full h-12 text-base font-semibold shadow-lg shadow-primary/20"
                        size="lg"
                    >
                        {isProcessing ? (
                            <span className="flex items-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Iniciando...
                            </span>
                        ) : (
                            <span className="flex items-center gap-2">
                                <Send className="w-4 h-4" /> Generar Render
                            </span>
                        )}
                    </Button>
                </div>
            </div>
        </aside>
    );
};
