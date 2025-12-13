export interface CameraAngle {
  id: string;
  label: string;
  description: string;
  promptMod: string;
}

export interface BriaFiboPayload {
  prompt: string;
  image_data?: string;
  camera_angle: string; // Will be mapped to brand_guidelines
  quantity: number;     // Will be mapped to variations
}

export interface GeneratedImage {
  id: string;
  url: string; // Data URL or Remote URL
  prompt_used: string;
}

export interface BriaFiboResponse {
  id: string;
  images: GeneratedImage[];
  rag_context?: string;
  content?: string;
  rag_sources?: string[];
  status: 'success' | 'error';
}

// Backend API Types
export type JobStage = 'BRIA_SP_REQUEST' | 'LLM_PATCHES' | 'IMAGE_POLL' | 'DONE' | 'ERROR';

export interface LogEventObject {
  t: string | number;
  msg: string;
}

export interface JobStatusResponse {
  stage: JobStage;
  progress: number;
  events: (string | LogEventObject)[];
  partial_results?: string[];
  results?: any[]; // Relaxed type to handle runtime variations (string or object)
  error?: string;
  trace?: string;
}

export interface GenerateResponse {
  job_id: string;
}