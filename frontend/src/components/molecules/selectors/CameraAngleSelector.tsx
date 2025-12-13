import React from 'react';
import { ArrowUp, ArrowDown, MoveDiagonal, Eye, Camera } from 'lucide-react';
import { CameraAngle } from '../../../types';

// Marketing focused camera angles definition
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

interface CameraAngleSelectorProps {
    selectedAngle: string;
    setSelectedAngle: (id: string) => void;
    isProcessing: boolean;
}

export const CameraAngleSelector: React.FC<CameraAngleSelectorProps> = ({ selectedAngle, setSelectedAngle, isProcessing }) => {
    return (
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
    );
};

export { CAMERA_ANGLES }; // Exporting in case it's needed elsewhere (e.g. App logic)
