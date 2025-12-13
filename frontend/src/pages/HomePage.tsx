import React, { useState } from 'react';
import { SidebarControls } from '../components/organisms/panels/SidebarControls';
import { GallerySidebar } from '../components/organisms/panels/GallerySidebar';
import { MainCanvas } from '../components/organisms/canvas/MainCanvas';
import { MainLayout } from '../components/templates/MainLayout';
import { CAMERA_ANGLES } from '../components/molecules/selectors/CameraAngleSelector';
import { startGenerationProcess } from '../services/geminiService';
import { GeneratedImage, JobStatusResponse } from '../types';

export const HomePage: React.FC = () => {
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

    // UI State
    const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true);
    const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true);
    const [isDarkMode, setIsDarkMode] = useState(true);

    // Derived state
    const activeImage = generatedImages.find(img => img.id === activeImageId) || generatedImages[0];

    const handleSubmit = async () => {
        console.log('[Marketech App] handleSubmit called');

        if (!prompt.trim() || !selectedImage) {
            setError("Se requiere una imagen y un prompt para iniciar.");
            return;
        }

        setIsProcessing(true);
        setError(null);
        setJobStatus(null);

        // Construct Payload
        const payload = {
            prompt: prompt,
            image_data: selectedImage,
            camera_angle: CAMERA_ANGLES.find(a => a.id === selectedAngle)?.promptMod || '',
            quantity: quantity
        };

        try {
            const results = await startGenerationProcess(payload, (status) => {
                setJobStatus(status);
            });

            console.log('[Marketech App] Generation results:', results);
            if (results && results.length > 0) {
                setGeneratedImages(prev => [...results, ...prev]);
                setActiveImageId(results[0].id);
            }
        } catch (err: any) {
            console.error('[Marketech App] Generation error:', err);
            setError(err.message || "Error desconocido durante la generación.");
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <MainLayout isDarkMode={isDarkMode}>
            <SidebarControls
                isOpen={isLeftSidebarOpen}
                setIsOpen={setIsLeftSidebarOpen}
                isDarkMode={isDarkMode}
                setIsDarkMode={setIsDarkMode}
                selectedImage={selectedImage}
                setSelectedImage={setSelectedImage}
                prompt={prompt}
                setPrompt={setPrompt}
                selectedAngle={selectedAngle}
                setSelectedAngle={setSelectedAngle}
                quantity={quantity}
                setQuantity={setQuantity}
                isProcessing={isProcessing}
                error={error}
                onSubmit={handleSubmit}
            />

            <MainCanvas
                isProcessing={isProcessing}
                jobStatus={jobStatus}
                activeImage={activeImage}
            />

            <GallerySidebar
                isOpen={isRightSidebarOpen}
                setIsOpen={setIsRightSidebarOpen}
                images={generatedImages}
                activeImageId={activeImageId}
                setActiveImageId={setActiveImageId}
                isProcessing={isProcessing}
            />
        </MainLayout>
    );
};
