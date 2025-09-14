import os
import re

def clean_filename(filename):
    """Generar nombre limpio y corto"""
    # Remover .pdf
    name = filename.replace('.pdf', '')
    
    # Extraer palabras clave importantes
    keywords = {
        'importa fácil': 'importa_facil',
        'entrega rápida': 'entrega_rapida', 
        'serpost': 'serpost',
        'aduanas': 'aduanas',
        'sunat': 'sunat',
        'constitución': 'constitucion',
        'empresa': 'empresa',
        'exportar': 'exportar',
        'importar': 'importar',
        'aranceles': 'aranceles',
        'documentos': 'documentos'
    }
    
    name_lower = name.lower()
    
    # Buscar palabras clave
    found_keywords = []
    for keyword, replacement in keywords.items():
        if keyword in name_lower:
            found_keywords.append(replacement)
    
    if found_keywords:
        new_name = '_'.join(found_keywords[:2])  # Máximo 2 palabras
    else:
        # Usar las primeras palabras significativas
        words = re.findall(r'\b\w+\b', name)
        significant_words = [w for w in words if len(w) > 3][:3]
        new_name = '_'.join(significant_words).lower()
    
    # Limpiar caracteres especiales
    new_name = re.sub(r'[^\w]', '_', new_name)
    new_name = re.sub(r'_+', '_', new_name)
    new_name = new_name.strip('_')[:25]  # Máximo 25 caracteres
    
    return new_name + '.pdf'

# Renombrar archivos en la carpeta docs
docs_path = "docs"
renamed_count = 0

print("🔄 Renombrando archivos PDF...")

for filename in os.listdir(docs_path):
    if filename.lower().endswith('.pdf'):
        old_path = os.path.join(docs_path, filename)
        new_filename = clean_filename(filename)
        new_path = os.path.join(docs_path, new_filename)
        
        if filename != new_filename:
            try:
                os.rename(old_path, new_path)
                print(f"✅ {filename} → {new_filename}")
                renamed_count += 1
            except Exception as e:
                print(f"❌ Error renombrando {filename}: {str(e)}")
        else:
            print(f"⚪ {filename} (sin cambios)")

print(f"\n🎉 {renamed_count} archivos renombrados exitosamente!")