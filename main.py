import requests
import json
import os
import re
from datetime import datetime, timedelta

# ==========================================
# 0. CONFIGURACIÓN DE SEGURIDAD (TOKEN)
# ==========================================
# Prioridad: 1. Secret de GitHub, 2. Token directo (Local)
TOKEN_API = os.getenv("MAGIC_TOKEN", "Mn1iiAAAAB1UI-aNNnM-7833")

# ==========================================
# 1. CONFIGURACIÓN DE SEASON Y TIEMPO
# ==========================================
# Fecha de referencia para el cálculo automático de temporadas
FECHA_INICIO_REF = datetime(2026, 3, 2, 0, 0)
SEASON_REF = 198

def calcular_info_season():
    ahora = datetime.now()
    dias_desde_inicio = (ahora - FECHA_INICIO_REF).days
    num_seasons_completas = dias_desde_inicio // 14
    id_actual = SEASON_REF + num_seasons_completas
    fecha_inicio_esta_season = FECHA_INICIO_REF + timedelta(days=num_seasons_completas * 14)
    fecha_final_esta_season = fecha_inicio_esta_season + timedelta(days=13, hours=23, minutes=59)
    return id_actual, fecha_final_esta_season

ID_SEASON, FECHA_CIERRE = calcular_info_season()
NOMBRE_SEASON = f"Season {ID_SEASON}"
FECHA_ISO_CIERRE = FECHA_CIERRE.strftime("%Y-%m-%dT%H:%M:%S")

# ==========================================
# 2. ESCÁNER HISTÓRICO (MODO COMPATIBILIDAD)
# ==========================================
def escanear_historial_cerrado():
    stats_medallas = {}
    records_puntos = []
    
    # Escanea desde la temporada 1 hasta la anterior a la actual
    for i in range(1, ID_SEASON + 1): 
        archivo = f"Season_{i}.html"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    contenido = f.read()
                    
                    # Detecta nombres en h2 (formato viejo) o h3 (formato nuevo)
                    nombres = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', contenido)
                    
                    # Detecta clase "points" (nuevo) o "pts" (viejo)
                    puntos_raw = re.findall(r'class="(?:points|pts)[^>]*>([\d,.]+)</', contenido)
                    
                    # 1. Procesar Medallero (Top 3 de cada archivo encontrado)
                    for idx, nombre in enumerate(nombres[:3]):
                        nom_limpio = nombre.strip().upper()
                        if nom_limpio not in stats_medallas:
                            stats_medallas[nom_limpio] = {'oro': 0, 'plata': 0, 'bronce': 0}
                        if idx == 0: stats_medallas[nom_limpio]['oro'] += 1
                        elif idx == 1: stats_medallas[nom_limpio]['plata'] += 1
                        elif idx == 2: stats_medallas[nom_limpio]['bronce'] += 1
                    
                    # 2. Procesar Récords Globales (Hall of Fame)
                    for idx, p_str in enumerate(puntos_raw):
                        if idx < len(nombres):
                            val_limpio = p_str.replace(',', '').replace('.', '')
                            val = int(val_limpio)
                            records_puntos.append({'pts': val, 'nom': nombres[idx].strip(), 's': i})
            except:
                continue
            
    # Ordenar por puntuación más alta
    records_puntos.sort(key=lambda x: x['pts'], reverse=True)
    return stats_medallas, records_puntos[:5]

MEDALLERO_HISTORICO, TOP_5_RECORDS = escanear_historial_cerrado()

# ==========================================
# 3. LLAMADA A LA API Y PROCESAMIENTO
# ==========================================
url = "https://ranking.amanotes.net/api/top"
headers = {
    "Accept": "*/*",
    "accesskey": TOKEN_API,
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "UnityPlayer/2021.3.45f2 (UnityWebRequest/1.0)",
}
payload = {"accessKey": TOKEN_API, "version": "13.022.001"}

try:
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        jugadores = data if isinstance(data, list) else data.get('ranking', data.get('data', []))

        # Filtrado por Blacklist
        if os.path.exists("blacklist.json"):
            with open("blacklist.json", "r") as f:
                try:
                    bl = json.load(f)
                    jugadores = [j for j in jugadores if f"UUID_{str(j.get('facebook_id'))[:8]}" not in bl]
                except: pass

        jugadores.sort(key=lambda x: x.get('battle_points', 0), reverse=True)

        # Generar HTML de los récords del Hall of Fame
        records_html = ""
        for idx, rec in enumerate(TOP_5_RECORDS):
            records_html += f"""
            <div class="flex-none glass px-4 py-2 rounded-xl border-b-2 border-white/10">
                <p class="text-[7px] font-bold text-cyan-300 uppercase tracking-tighter"># {idx+1} RECORD (S-{rec['s']})</p>
                <p class="text-xs font-black italic uppercase">{rec['nom']}</p>
                <p class="points text-sm leading-none">{rec['pts']:,}</p>
            </div>"""

        # --- CONSTRUCCIÓN DEL HTML FINAL ---
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Magic Ranking | {NOMBRE_SEASON}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;700;900&display=swap');
        body {{ background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); background-attachment: fixed; color: #ffffff; font-family: 'Inter', sans-serif; min-height: 100vh; }}
        .points {{ font-family: 'Orbitron', sans-serif; text-shadow: 0 0 10px rgba(0, 210, 255, 0.5); }}
        .glass {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); }}
        .badge-mini {{ font-size: 10px; font-weight: 900; padding: 2px 6px; border-radius: 4px; margin-left: 5px; }}
        .b-oro {{ background: #ffd700; color: #000; }}
        .b-plata {{ background: #e5e5e5; color: #000; }}
        .b-bronce {{ background: #cd7f32; color: #fff; }}
        .admin-only-id {{ display: none; }}
        .top-1 {{ border-left: 4px solid #ffd700; background: linear-gradient(90deg, rgba(255,215,0,0.1), transparent); }}
        .no-scrollbar::-webkit-scrollbar {{ display: none; }}
    </style>
</head>
<body class="p-4 md:p-10">
    <div class="max-w-4xl mx-auto">
        <header class="flex justify-between items-end mb-8">
            <div>
                <p class="text-[10px] font-black uppercase tracking-widest text-cyan-400">LIVE LEADERBOARD</p>
                <div class="flex items-center gap-4">
                    <h1 class="text-4xl md:text-6xl font-black italic uppercase italic">S-{ID_SEASON}</h1>
                    <select id="seasonSelector" class="bg-black/40 border border-white/20 text-[10px] rounded px-2 py-1" onchange="if(this.value!='#') window.location.href=this.value"></select>
                </div>
            </div>
            <div class="text-right glass p-4 rounded-2xl">
                <p class="text-[9px] font-bold text-white/50">ENDS IN:</p>
                <div id="countdown" class="text-xl md:text-2xl font-black points">--:--:--</div>
            </div>
        </header>

        <div class="mb-10">
            <p class="text-[10px] font-black text-white/40 mb-4 italic tracking-widest">HALL OF FAME (ALL TIME RECORDS)</p>
            <div class="flex gap-4 overflow-x-auto no-scrollbar">
                {records_html or '<p class="text-xs opacity-20">Scanning archives...</p>'}
            </div>
        </div>

        <div class="space-y-3">
        """

        for i, p in enumerate(jugadores, 1):
            fb_id = str(p.get('facebook_id', ''))
            nombre = p.get('facebook_name', 'Jugador')
            nombre_upper = nombre.strip().upper()
            bp = p.get('battle_points', 0)
            btls = p.get('total_battle', 0)
            wins = p.get('total_win', 0)
            wr = (wins / btls * 100) if btls > 0 else 0
            pais = p.get('country', '??').lower()
            
            # Cargar medallas del historial
            h = MEDALLERO_HISTORICO.get(nombre_upper, {'oro': 0, 'plata': 0, 'bronce': 0})
            badges = ""
            if h['oro'] > 0: badges += f'<span class="badge-mini b-oro">🥇 {h["oro"]}</span>'
            if h['plata'] > 0: badges += f'<span class="badge-mini b-plata">🥈 {h["plata"]}</span>'
            if h['bronce'] > 0: badges += f'<span class="badge-mini b-bronce">🥉 {h["bronce"]}</span>'

            icon = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            row_class = "top-1" if i == 1 else "glass"

            html_content += f"""
            <div class="flex flex-col md:flex-row items-center p-4 rounded-xl {row_class} gap-4">
                <div class="w-12 text-center text-xl font-black italic text-white/30">{icon}</div>
                <div class="flex items-center gap-4 flex-1 w-full">
                    <img src="https://graph.facebook.com/{fb_id}/picture?type=large" class="w-14 h-14 rounded-full border-2 border-white/20 object-cover" onerror="this.src='https://ui-avatars.com/api/?name={nombre}';">
                    <div class="min-w-0">
                        <div class="flex items-center gap-2">
                            <h2 class="text-lg font-black uppercase italic truncate">{nombre}</h2>
                            <img src="https://flagcdn.com/w20/{pais}.png" class="rounded-sm">
                        </div>
                        <div class="flex mt-1">{badges}</div>
                        <span class="admin-only-id">UUID_{fb_id[:8]}</span>
                    </div>
                </div>
                <div class="flex gap-8 text-center bg-black/20 p-3 rounded-lg w-full md:w-auto">
                    <div><p class="text-[8px] text-white/40 uppercase font-black">Matches</p><p class="font-bold text-xs">{btls}</p></div>
                    <div><p class="text-[8px] text-green-400 uppercase font-black">WR</p><p class="font-bold text-xs">{wr:.1f}%</p></div>
                    <div class="flex-1 md:text-right">
                        <p class="text-[8px] text-cyan-400 uppercase font-black">Score</p>
                        <p class="points text-xl leading-none">{bp:,}</p>
                    </div>
                </div>
            </div>"""

        html_content += """
        </div>
    </div>
    <script>
        // Lógica del selector de temporadas
        const currentS = """ + str(ID_SEASON) + """;
        const sel = document.getElementById('seasonSelector');
        let h_opt = document.createElement('option'); h_opt.value='#'; h_opt.innerText='HISTORIAL'; sel.appendChild(h_opt);
        for(let i = currentS; i >= 180; i--) {
            let opt = document.createElement('option');
            opt.value = i === currentS ? 'index.html' : `Season_${i}.html`;
            opt.innerText = `Temporada ${i}`;
            if(window.location.href.includes(opt.value)) opt.selected = true;
            sel.appendChild(opt);
        }

        // Lógica del Countdown
        const targetDate = new Date(""" + f'"{FECHA_ISO_CIERRE}"' + """).getTime();
        function updateTimer() {
            const now = new Date().getTime();
            const diff = targetDate - now;
            if (diff < 0) { document.getElementById("countdown").innerHTML = "CLOSED"; return; }
            const d = Math.floor(diff / (1000 * 60 * 60 * 24));
            const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const s = Math.floor((diff % (1000 * 60)) / 1000);
            document.getElementById("countdown").innerHTML = `${d}D ${h}H ${m}M ${s}S`;
        }
        setInterval(updateTimer, 1000); updateTimer();
    </script>
</body>
</html>"""

        # Guardado de archivos
        with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
        with open(f"Season_{ID_SEASON}.html", "w", encoding="utf-8") as f: f.write(html_content)
        print(f"✅ Ranking actualizado: {NOMBRE_SEASON}")

except Exception as e:
    print(f"❌ Error fatal: {e}")
