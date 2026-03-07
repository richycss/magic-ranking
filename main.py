# ... (Todo el inicio del código se mantiene igual hasta la función de escaneo)

# ==========================================
# 2. ESCÁNER HISTÓRICO (CORREGIDO PARA DETECTAR "PTS" Y "POINTS")
# ==========================================
def escanear_historial_cerrado():
    stats_medallas = {}
    records_puntos = []
    
    # Escaneamos archivos desde la 1 hasta la actual
    for i in range(1, ID_SEASON): 
        archivo = f"Season_{i}.html"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    contenido = f.read()
                    
                    # 1. Buscar nombres (Detecta h2 y h3)
                    nombres = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', contenido)
                    
                    # 2. Buscar puntos (Detecta tanto class="points" como class="pts")
                    # Esta nueva regex es más flexible
                    puntos_raw = re.findall(r'class="(?:points|pts)[^>]*>([\d,.]+)</', contenido)
                    
                    # Procesar Medallero (Top 3)
                    for idx, nombre in enumerate(nombres[:3]):
                        nom_limpio = nombre.strip().upper()
                        if nom_limpio not in stats_medallas:
                            stats_medallas[nom_limpio] = {'oro': 0, 'plata': 0, 'bronce': 0}
                        if idx == 0: stats_medallas[nom_limpio]['oro'] += 1
                        elif idx == 1: stats_medallas[nom_limpio]['plata'] += 1
                        elif idx == 2: stats_medallas[nom_limpio]['bronce'] += 1
                    
                    # Procesar Récords Globales
                    for idx, p_str in enumerate(puntos_raw):
                        if idx < len(nombres):
                            # Limpiar comas o puntos para convertir a número
                            val_limpio = p_str.replace(',', '').replace('.', '')
                            val = int(val_limpio)
                            records_puntos.append({
                                'pts': val, 
                                'nom': nombres[idx].strip(), 
                                's': i
                            })
            except Exception as e:
                print(f"Error procesando {archivo}: {e}")
                continue
            
    # Ordenar de mayor a menor y tomar los 5 mejores
    records_puntos.sort(key=lambda x: x['pts'], reverse=True)
    return stats_medallas, records_puntos[:5]

# ... (El resto del script hacia abajo sigue igual)
