import React, { useCallback, useState } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';

interface ImageUploaderProps {
  onImageSelected: (base64: string | null) => void;
  selectedImage: string | null;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({ onImageSelected, selectedImage }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      onImageSelected(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const removeImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    onImageSelected(null);
  };

  if (selectedImage) {
    return (
      <div className="relative w-full h-40 rounded-lg overflow-hidden border border-border group">
        <img src={selectedImage} alt="Reference" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <button
            onClick={removeImage}
            className="p-2 bg-white/10 backdrop-blur-md hover:bg-red-500/80 rounded-full text-white transition-all"
          >
            <X size={18} />
          </button>
        </div>
        <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-[10px] text-white font-medium">
          Referencia
        </div>
      </div>
    );
  }

  return (
    <div
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      className={`relative flex flex-col items-center justify-center w-full h-32 rounded-lg border-2 border-dashed transition-all duration-200 cursor-pointer 
      ${isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/20 hover:border-primary/50 hover:bg-muted/30'}
      `}
    >
      <label htmlFor="image-upload" className="flex flex-col items-center justify-center w-full h-full cursor-pointer p-4 text-center">
        <ImageIcon className="w-6 h-6 mb-2 text-muted-foreground" />
        <p className="text-xs text-muted-foreground font-medium">Subir Referencia</p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">Arrastra o Click</p>
        <input id="image-upload" type="file" className="hidden" accept="image/*" onChange={onFileInput} />
      </label>
    </div>
  );
};