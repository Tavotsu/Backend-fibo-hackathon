import json

# Cargar el notebook
with open('backend/BRIA_Backend.ipynb', 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Extraer celda 3 (microservicio)
code_cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
celda_3 = ''.join(code_cells[2].get('source', []))

# Guardar en archivo
with open('celda_3_microservicio.py', 'w', encoding='utf-8') as f:
    f.write(celda_3)

print("Celda 3 extraída a: celda_3_microservicio.py")
print(f"Tamaño: {len(celda_3)} caracteres")
