import React, { useState, useEffect, useRef } from 'react';
import { ImageUploader } from './components/ImageUploader';
import { Button } from './components/ui/Button';
import { Textarea } from './components/ui/Textarea';
import { startGenerationProcess } from './services/geminiService';
import { GeneratedImage, CameraAngle, JobStatusResponse } from './types';
import {
  Cpu,
  Send,
  Layers,
  Maximize2,
  Download,
  Eye,
  Camera,
  MoveDiagonal,
  ArrowUp,
  ArrowDown,
  MonitorPlay,
  AlertCircle,
  Loader2,
  Terminal,
  CheckCircle2
} from 'lucide-react';

// Marketing focused camera angles
const CAMERA_ANGLES: CameraAngle[] = [
  {
    id: 'eye-level',
    label: 'Eye Level',
    description: 'Conexión y confianza',
    promptMod: 'Shot at eye-level, approachable, trustworthy'
  },
  {
    id: 'low-angle',
    label: 'Heroic Low',
    description: 'Poder y autoridad',
    promptMod: 'Low angle shot looking up, heroic, empowering'
  },
  {
    id: 'overhead',
    label: 'Flat Lay',
    description: 'Detalle de producto',
    promptMod: 'Overhead flat lay shot, organized, clean composition'
  },
  {
    id: 'dutch',
    label: 'Dutch Angle',
    description: 'Dinamismo',
    promptMod: 'Dutch angle (tilted), dynamic energy, edgy'
  },
  {
    id: 'macro',
    label: 'Macro Detail',
    description: 'Calidad y textura',
    promptMod: 'Macro close-up shot, focus on texture'
  }
];

const getIconForAngle = (id: string) => {
  switch (id) {
    case 'low-angle': return <ArrowUp className="w-4 h-4" />;
    case 'overhead': return <ArrowDown className="w-4 h-4" />;
    case 'dutch': return <MoveDiagonal className="w-4 h-4" />;
    case 'macro': return <Eye className="w-4 h-4" />;
    default: return <Camera className="w-4 h-4" />;
  }
};

const App: React.FC = () => {
  // State
  const [prompt, setPrompt] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedAngle, setSelectedAngle] = useState<string>('eye-level');
  const [quantity, setQuantity] = useState<number>(4);

  const [isProcessing, setIsProcessing] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const [activeImageId, setActiveImageId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Derived state for the main display
  const activeImage = generatedImages.find(img => img.id === activeImageId) || generatedImages[0];
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [jobStatus?.events]);

  const handleSubmit = async () => {
    console.log('[Marketech App] handleSubmit called');
    console.log('[Marketech App] prompt:', prompt);
    console.log('[Marketech App] selectedImage:', !!selectedImage);

    if (!prompt.trim() || !selectedImage) {
      setError("Se requiere una imagen y un prompt para iniciar.");
      console.log('[Marketech App] Validation failed - missing prompt or image');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setJobStatus(null);

    // Construct Payload for Backend
    const payload = {
      prompt: prompt,
      image_data: selectedImage,
      camera_angle: CAMERA_ANGLES.find(a => a.id === selectedAngle)?.promptMod || '',
      quantity: quantity
    };
    console.log('[Marketech App] Payload prepared, calling startGenerationProcess');

    try {
      // API URL is now hardcoded in service
      const results = await startGenerationProcess(payload, (status) => {
        console.log('[Marketech App] Progress update:', status.stage, status.progress);
        setJobStatus(status);
      });

      console.log('[Marketech App] Generation completed, results:', results);
      if (results && results.length > 0) {
        console.log('[Marketech App] Setting', results.length, 'images to state');
        setGeneratedImages(prev => [...results, ...prev]);
        setActiveImageId(results[0].id);
      } else {
        console.log('[Marketech App] No results returned');
      }
    } catch (err: any) {
      console.error('[Marketech App] Generation error:', err);
      setError(err.message || "Error desconocido durante la generación.");
    } finally {
      setIsProcessing(false);
      console.log('[Marketech App] Process finished');
    }
  };

  return (
    <div className="flex h-screen w-full bg-zinc-950 text-zinc-100 font-sans overflow-hidden">

      {/* LEFT SIDEBAR - CONTROLS */}
      <aside className="w-80 md:w-96 flex flex-col border-r border-zinc-800 bg-zinc-900/50 backdrop-blur-sm z-10">

        {/* Header */}
        <div className="p-5 border-b border-zinc-800 flex items-center gap-2">
          <div className="p-1.5 bg-primary rounded-md">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-none tracking-tight">Marketech</h1>
            <p className="text-[10px] text-zinc-400 font-medium tracking-wide">Modelo 0.1a</p>
          </div>
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
              className="min-h-[100px] resize-none bg-zinc-950/50 border-zinc-800 focus:border-primary/50 transition-colors"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isProcessing}
            />
          </div>

          {/* Camera Angles */}
          <div className="space-y-3">
            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center justify-between">
              <span>Ángulo de Cámara</span>
              <span className="text-[10px] text-primary">Marketing Focused</span>
            </label>
            <div className="grid grid-cols-1 gap-2">
              {CAMERA_ANGLES.map((angle) => (
                <button
                  key={angle.id}
                  onClick={() => !isProcessing && setSelectedAngle(angle.id)}
                  disabled={isProcessing}
                  className={`flex items-center p-2.5 rounded-md border transition-all text-left group
                    ${selectedAngle === angle.id
                      ? 'bg-primary/10 border-primary text-primary shadow-[0_0_10px_rgba(var(--primary),0.2)]'
                      : 'bg-zinc-800/50 border-transparent hover:bg-zinc-800 hover:border-zinc-700 text-zinc-400'}
                    ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  <div className={`p-2 rounded-full mr-3 ${selectedAngle === angle.id ? 'bg-primary text-white' : 'bg-zinc-700 text-zinc-400 group-hover:bg-zinc-600'}`}>
                    {getIconForAngle(angle.id)}
                  </div>
                  <div>
                    <div className="text-sm font-medium">{angle.label}</div>
                    <div className="text-[10px] opacity-70">{angle.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Quantity */}
          <div className="space-y-3">
            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              Cantidad de Variaciones
            </label>
            <div className="flex gap-2">
              {[1, 2, 3, 4].map((num) => (
                <button
                  key={num}
                  onClick={() => !isProcessing && setQuantity(num)}
                  disabled={isProcessing}
                  className={`flex-1 h-9 rounded-md text-sm font-medium border transition-all
                    ${quantity === num
                      ? 'bg-zinc-100 text-zinc-900 border-zinc-100'
                      : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-600'}
                    ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-3 bg-red-900/20 border border-red-900/50 rounded-md text-red-200 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <div>{error}</div>
            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div className="p-5 border-t border-zinc-800 bg-zinc-900/80">
          <Button
            onClick={handleSubmit}
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
      </aside>

      {/* MAIN CANVAS AREA */}
      <main className="flex-1 flex flex-col h-full relative bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-zinc-900 via-zinc-950 to-zinc-950">

        {/* Top Toolbar */}
        <div className="h-16 border-b border-zinc-800/50 flex items-center justify-between px-6 bg-zinc-950/50 backdrop-blur-sm absolute top-0 w-full z-10">
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
          {activeImage && !isProcessing && (
            <Button variant="outline" size="sm" className="gap-2 h-8 border-zinc-700 hover:bg-zinc-800 text-zinc-300">
              <Download className="w-3.5 h-3.5" /> Exportar HD
            </Button>
          )}
        </div>

        {/* Canvas Center */}
        <div className="flex-1 flex items-center justify-center p-8 overflow-hidden relative">

          {isProcessing ? (
            /* LOADING SCREEN OVERLAY */
            <div className="w-full max-w-lg p-8 rounded-xl bg-zinc-900/80 border border-zinc-800 backdrop-blur-xl shadow-2xl flex flex-col gap-6 animate-in fade-in zoom-in-95 duration-500">

              <div className="flex flex-col items-center justify-center space-y-4">
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse" />
                  <Loader2 className="w-12 h-12 text-primary animate-spin relative z-10" />
                </div>
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-white tracking-tight">Generando Assets</h3>
                  <p className="text-sm text-zinc-400">El modelo está interpretando tu prompt...</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs uppercase tracking-wider font-bold text-zinc-500">
                  <span>Progreso del Job</span>
                  <span>{jobStatus ? Math.round(jobStatus.progress) : 0}%</span>
                </div>
                <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-600 to-primary transition-all duration-300 ease-out"
                    style={{ width: `${jobStatus ? jobStatus.progress : 0}%` }}
                  />
                </div>
              </div>

              <div className="bg-black/50 rounded-md border border-zinc-800/50 p-4 font-mono text-xs text-zinc-400 h-48 flex flex-col">
                <div className="flex items-center gap-2 border-b border-zinc-800/50 pb-2 mb-2 text-zinc-500">
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
                    <span className="text-zinc-700 italic">Esperando conexión al servidor...</span>
                  )}
                  <div ref={logsEndRef} />
                </div>
              </div>

            </div>
          ) : activeImage ? (
            <div className="relative group max-w-full max-h-full flex flex-col items-center">
              <div className="relative shadow-2xl shadow-black rounded-lg overflow-hidden border border-zinc-800 bg-zinc-900/50 backdrop-blur-3xl">
                <img
                  src={activeImage.url}
                  alt="Generated content"
                  className="max-h-[calc(100vh-140px)] max-w-full object-contain animate-in fade-in zoom-in-95 duration-500"
                />
                <div className="absolute inset-0 ring-1 ring-white/10 pointer-events-none rounded-lg" />
              </div>
            </div>
          ) : (
            <div className="text-center space-y-4 opacity-30 select-none">
              <div className="w-32 h-32 mx-auto rounded-full border-4 border-dashed border-zinc-700 flex items-center justify-center">
                <Maximize2 className="w-12 h-12 text-zinc-700" />
              </div>
              <p className="text-xl font-medium text-zinc-500">El canvas está vacío</p>
              <p className="text-sm text-zinc-600">Configura los parámetros a la izquierda para comenzar</p>
            </div>
          )}
        </div>

      </main>

      {/* RIGHT SIDEBAR - GALLERY */}
      <aside className="w-24 md:w-32 border-l border-zinc-800 bg-zinc-900/80 backdrop-blur-sm flex flex-col z-10">
        <div className="p-4 border-b border-zinc-800">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest block text-center">
            Galería
          </span>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
          {generatedImages.map((img) => (
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

          {generatedImages.length === 0 && !isProcessing && (
            <div className="text-[10px] text-zinc-600 text-center mt-10 px-2">
              Sin Imágenes
            </div>
          )}
        </div>
      </aside>

    </div>
  );
};

export default App;