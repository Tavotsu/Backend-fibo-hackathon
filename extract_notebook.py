import json
import sys

# Cargar el notebook
with open('backend/BRIA_Backend.ipynb', 'r', encoding='utf-8') as f:
    notebook = json.load(f)

print(f"Total de celdas: {len(notebook['cells'])}")
print("\n=== Primeras 10 celdas de código ===\n")

code_cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
for i, cell in enumerate(code_cells[:10]):
    source = ''.join(cell.get('source', []))
    print(f"\n--- Celda {i+1} ---")
    print(source[:500])  # Primeros 500 caracteres
    if len(source) > 500:
        print("... (truncado)")
