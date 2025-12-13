import { BriaFiboPayload, GeneratedImage, JobStatusResponse } from "../types";

// Backend URL - cambiar a ngrok cuando se despliegue
const API_BASE_URL = "http://localhost:8001";

/**
 * Utility to convert Base64 string to Blob for FormData
 */
const base64ToBlob = async (base64: string): Promise<Blob> => {
  const res = await fetch(base64);
  return await res.blob();
};

/**
 * Securely fetch image to bypass ngrok warning and handle relative paths
 */
/**
 * Securely fetch image to bypass ngrok warning and handle relative paths
 */
const fetchSecureImage = async (urlPath: string): Promise<string> => {
  // Validación de entrada
  if (!urlPath || typeof urlPath !== 'string') {
    console.warn("Invalid urlPath passed to fetchSecureImage:", urlPath);
    // Si es un objeto con propiedad url, intentar usarla
    if (typeof urlPath === 'object' && urlPath !== null && (urlPath as any).url) {
      return fetchSecureImage((urlPath as any).url);
    }
    return '';
  }

  // Limpiar espacios en blanco de la URL
  const cleanUrl = urlPath.trim();
  if (!cleanUrl) return '';

  // Si es una URL externa completa (Bria, S3, etc), devolverla directamente
  // No intentamos hacer fetch para evitar problemas de CORS
  if (cleanUrl.startsWith('http://') || cleanUrl.startsWith('https://')) {
    // Solo procesar para convertir a blob si es nuestra API (ngrok o localhost)
    if (cleanUrl.includes("ngrok") || cleanUrl.includes("localhost")) {
      try {
        const res = await fetch(cleanUrl, {
          headers: {
            'ngrok-skip-browser-warning': '1',
          },
        });

        if (res.ok) {
          const blob = await res.blob();
          return URL.createObjectURL(blob);
        }
      } catch (e) {
        console.warn("Error fetching local image blob:", e);
      }
    }
    // Para URLs externas, devolverlas directamente
    return cleanUrl;
  }

  // Si es una ruta relativa, construir URL completa
  try {
    const cleanBase = API_BASE_URL.replace(/\/$/, "");
    const path = cleanUrl.startsWith('/') ? cleanUrl : `/${cleanUrl}`;
    const fullUrl = `${cleanBase}${path}`;

    // Intentar fetch con headers para bypass de ngrok
    const res = await fetch(fullUrl, {
      headers: {
        'ngrok-skip-browser-warning': '1',
      },
    });

    if (!res.ok) {
      console.warn(`Failed to fetch image, status: ${res.status}. Using URL directly.`);
      return fullUrl;
    }

    const blob = await res.blob();
    return URL.createObjectURL(blob);
  } catch (e) {
    console.error("Error fetching image blob:", e);
    const cleanBase = API_BASE_URL.replace(/\/$/, "");
    return `${cleanBase}/${cleanUrl.replace(/^\//, "")}`;
  }
};

/**
 * Check if backend is healthy
 */
const checkHealth = async (): Promise<boolean> => {
  try {
    // Ensure no trailing slash
    const cleanUrl = API_BASE_URL.replace(/\/$/, "");

    // Attempt health check with CORS mode and ngrok header
    const res = await fetch(`${cleanUrl}/health`, {
      method: 'GET',
      headers: {
        'ngrok-skip-browser-warning': '1',
      },
    });

    if (!res.ok) {
      console.warn(`Health Check failed with status: ${res.status} ${res.statusText}`);
      return false;
    }

    const data = await res.json();
    return data.status === "ok";
  } catch (e) {
    console.error("Health check network error:", e);
    return false;
  }
};

/**
 * Main function to orchestrate the generation flow
 */
export const startGenerationProcess = async (
  payload: BriaFiboPayload,
  onProgress: (status: JobStatusResponse) => void
): Promise<GeneratedImage[]> => {
  console.log('[Marketech] Starting generation process with payload:', {
    prompt: payload.prompt,
    hasImage: !!payload.image_data,
    camera_angle: payload.camera_angle,
    quantity: payload.quantity
  });

  const cleanUrl = API_BASE_URL.replace(/\/$/, "");
  console.log('[Marketech] API URL:', cleanUrl);

  // 1. Health Check
  onProgress({ stage: 'BRIA_SP_REQUEST', progress: 5, events: [`Connecting to secure backend...`] });

  // We perform the health check but provide a more descriptive error if it fails
  console.log('[Marketech] Checking backend health...');
  const isHealthy = await checkHealth();
  console.log('[Marketech] Health check result:', isHealthy);

  if (!isHealthy) {
    throw new Error("Conexión fallida con Bria Fibo. Verifique que el túnel de Ngrok esté activo y sea accesible.");
  }

  // 2. Prepare Form Data
  onProgress({ stage: 'BRIA_SP_REQUEST', progress: 10, events: ['Processing input data...'] });
  const formData = new FormData();

  if (payload.image_data) {
    console.log('[Marketech] Converting image to blob...');
    const blob = await base64ToBlob(payload.image_data);
    formData.append("image", blob, "input_image.png");
    console.log('[Marketech] Image blob added to form');
  }

  formData.append("prompt", payload.prompt);
  formData.append("brand_guidelines", `Camera Angle: ${payload.camera_angle}. Style: Premium and Creative.`);
  formData.append("variations", payload.quantity.toString());
  formData.append("aspect_ratio", "1:1");

  // 3. Start Generation
  onProgress({ stage: 'BRIA_SP_REQUEST', progress: 20, events: ['Sending secure payload...'] });
  console.log('[Marketech] Sending generation request to:', `${cleanUrl}/api/v1/generate-async`);

  let job_id: string;
  try {
    const res = await fetch(`${cleanUrl}/api/v1/generate-async`, {
      method: 'POST',
      headers: {
        'ngrok-skip-browser-warning': '1',
      },
      body: formData,
    });

    console.log('[Marketech] Generation response status:', res.status);
    if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
    const data = await res.json();
    job_id = data.job_id;
    console.log('[Marketech] Job started with ID:', job_id);
  } catch (e) {
    console.error('[Marketech] Failed to start generation:', e);
    throw new Error(`Failed to start generation job: ${e}`);
  }

  // 4. Poll for Status
  console.log('[Marketech] Starting polling for job:', job_id);
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const res = await fetch(`${cleanUrl}/api/v1/jobs/${job_id}`, {
          headers: {
            'ngrok-skip-browser-warning': '1',
          },
        });
        if (!res.ok) {
          throw new Error("Polling failed");
        }

        const status: JobStatusResponse = await res.json();
        console.log('[Marketech] Poll status:', status.stage, 'Progress:', status.progress);

        onProgress(status);

        if (status.stage === 'DONE') {
          const results = status.results || [];
          console.log('[Marketech] Job completed, processing results:', results);

          // Process results: convert paths to absolute and fetch blobs to bypass ngrok warning
          const processedImagesPromises = results.map(async (item: any): Promise<GeneratedImage | null> => {
            let urlStr = '';

            // Handle different result formats (string or object)
            if (typeof item === 'string') {
              urlStr = item;
            } else if (item && typeof item === 'object') {
              // Try common property names for image URLs
              urlStr = item.url || item.uri || item.path || item.image_url || item.result_url || '';

              if (!urlStr) {
                console.warn("[Marketech] Unknown result item format:", JSON.stringify(item));
              }
            }

            if (!urlStr) {
              console.warn("[Marketech] No URL found for item:", item);
              return null;
            }

            console.log('[Marketech] Processing image URL:', urlStr);
            const secureUrl = await fetchSecureImage(urlStr);

            if (!secureUrl) {
              console.warn("[Marketech] fetchSecureImage returned empty for:", urlStr);
              return null;
            }

            console.log('[Marketech] Secure URL created:', secureUrl.substring(0, 100));
            return {
              id: crypto.randomUUID(),
              url: secureUrl,
              prompt_used: payload.prompt
            };
          });

          const processedImages = await Promise.all(processedImagesPromises);

          // Filter out failed items
          const validImages = processedImages.filter((img): img is GeneratedImage => img !== null && !!img.url);
          console.log('[Marketech] Valid images count:', validImages.length);

          resolve(validImages);
        } else if (status.stage === 'ERROR') {
          reject(new Error(status.error || "Unknown backend error"));
        } else {
          setTimeout(poll, 1000);
        }
      } catch (e) {
        reject(e);
      }
    };

    poll();
  });
};