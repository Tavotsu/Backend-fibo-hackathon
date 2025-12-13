from pathlib import Path
from typing import Optional
from app.core.config import settings

class SimpleRAG:
    """
    Sistema RAG simple para cargar contexto de marca.
    """
    def __init__(self):
        self.kb_path = Path("app/rag/kb.txt")
        self.max_chars = 4000

    def load_context(self, extra_guidelines: Optional[str]) -> str:
        """Carga el contexto combinando KB y guidelines extra."""
        chunks = []
        
        # Intentar cargar KB del disco
        if self.kb_path.exists():
            try:
                chunks.append(self.kb_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Warning: Could not read KB file: {e}")
        
        # Agregar guidelines del usuario
        if extra_guidelines:
            chunks.append(extra_guidelines)
            
        ctx = "\n\n".join([c.strip() for c in chunks if c and c.strip()]).strip()
        
        # Truncar si es muy largo
        if len(ctx) > self.max_chars:
            return ctx[: self.max_chars] + "\n\n[...truncado...]"
        return ctx
