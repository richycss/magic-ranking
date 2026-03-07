import requests
import json
import os
import re
import sys
from datetime import datetime, timedelta

# ==========================================
# 0. CONFIGURACIÓN DE SEGURIDAD (TOKEN)
# ==========================================
# Busca el token en los Secrets de GitHub, si no existe (PC local), usa el de respaldo.
TOKEN_API = os.getenv("MAGIC_TOKEN", "Mn1iiAAAAB1UI-aNNnM-7833")

# ==========================================
# 1. CONFIGURACIÓN DE SEASON Y TIEMPO
# ==========================================
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
# 2. ESCÁNER HISTÓRICO (SOLO CERRADAS)
# ==========================================
def escanear_historial_cerrado():
    stats_medallas = {}
    records_puntos = []
    # Escaneamos archivos locales guardados en el repositorio
    for i in range(1, ID_SEASON): 
        archivo = f"Season_{i}.html"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    contenido = f.read()
                    nombres = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', contenido)
                    for idx, nombre in enumerate(nombres[:3]):
                        nom_limpio = nombre.strip().upper()
                        if nom_limpio not in stats_medallas:
                            stats_medallas[nom_limpio] = {'oro': 0, 'plata': 0, 'bronce': 0}
                        if idx == 0: stats_medallas[nom_limpio]['oro'] += 1
                        elif idx == 1: stats_medallas[nom_limpio]['plata'] += 1
                        elif idx == 2: stats_medallas[nom_limpio]['bronce'] += 1
                    
                    puntos_raw = re.findall(r'class="points[^>]*>([\d,]+)</div>', contenido)
                    for idx, p_str in enumerate(puntos_raw):
                        if idx < len(nombres):
                            val = int(p_str.replace(',', ''))
                            records_puntos.append({'pts': val, 'nom': nombres[idx].strip(), 's': i})
            except: continue
            
    records_puntos.sort(key=lambda x: x['pts'], reverse=True)
    return stats_medallas, records_puntos[:5]

MEDALLERO_HISTORICO, TOP_5_RECORDS = escanear_historial_cerrado()

# ==========================================
# 3. API Y PROCESAMIENTO
# ==========================================
url = "https://ranking.amanotes.net/api/top"
headers = {
    "Accept": "*/*",
    "accesskey": TOKEN_API,
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "UnityPlayer/2021.3.45f2 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
}
payload = {"accessKey": TOKEN_API, "version": "13.022.001"}

try:
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        jugadores = data if isinstance(data, list) else data.get('ranking', data.get('data', []))

        # Blacklist segura
        if os.path.exists("blacklist.json"):
            with open("blacklist.json", "r") as f:
                try:
                    bl = json.load(f)
                    jugadores = [j for j in jugadores if f"UUID_{str(j.get('facebook_id'))[:8]}" not in bl]
                except: pass

        jugadores.sort(key=lambda x: x.get('battle_points', 0), reverse=True)

        records_html = ""
        for idx, rec in enumerate(TOP_5_RECORDS):
            records_html += f"""
            <div class="flex-none glass px-4 py-2 rounded-xl border-b-2 border-white/10">
                <p class="text-[7px] font-bold text-cyan-300 uppercase tracking-tighter"># {idx+1} RECORD</p>
                <p class="text-xs font-black italic uppercase">{rec['nom']}</p>
                <p class="points text-sm leading-none">{rec['pts']:,}</p>
            </div>"""

        # --- HTML FINAL ---
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
        body {{ background: linear-gradient(180deg, #00c6ff 0%, #0072ff 40%, #bc4e9c 100%); background-attachment: fixed; color: #ffffff; font-family: 'Inter', sans-serif; min-height: 100vh; overflow-x: hidden; }}
        .points {{ font-family: 'Orbitron', sans-serif; text-shadow: 0 0 10px rgba(0, 210, 255, 0.7); }}
        .glass {{ background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.15); }}
        .badge-mini {{ font-size: 9px; font-weight: 900; padding: 1px 5px; border-radius: 4px; margin-left: 4px; display: inline-flex; align-items: center; gap: 2px; }}
        .b-oro {{ background: #ffd700; color: #000; }}
        .b-plata {{ background: #e5e5e5; color: #000; }}
        .b-bronce {{ background: #cd7f32; color: #fff; }}
        .admin-only-id {{ display: none; }}
        @media (max-width: 767px) {{
            .r-tr {{ display: flex; flex-direction: column; padding: 0.8rem; margin-bottom: 0.5rem; border-radius: 1rem; }}
            .order-3-m {{ order: 0; display: flex; justify-content: space-between; align-items: center; }}
            .order-1-m {{ order: 1; margin: 0.5rem 0; }}
            .order-2-m {{ order: 2; border-top: 1px solid rgba(255,255,255,0.1); pt-2; }}
        }}
        .top-1 {{ background: linear-gradient(90deg, rgba(255, 215, 0, 0.25) 0%, rgba(255,255,255,0.1) 100%) !important; border-left: 4px solid #ffd700; }}
        select {{ background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.3); color: white; border-radius: 8px; font-size: 11px; padding: 4px; }}
        .no-scrollbar::-webkit-scrollbar {{ display: none; }}
    </style>
</head>
<body class="p-2 md:p-10">
    <div class="max-w-4xl mx-auto">
        <header class="flex justify-between items-end mb-6 px-2">
            <div>
                <p class="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-200">MAGIC LEADERBOARD</p>
                <div class="flex items-center gap-3">
                    <h1 class="text-4xl md:text-6xl font-black italic uppercase text-white">S-{ID_SEASON}</h1>
                    <select id="seasonSelector" onchange="if(this.value!='#') window.location.href=this.value"></select>
                </div>
            </div>
            <div class="text-right glass p-3 rounded-2xl border-l-4 border-cyan-400">
                <p class="text-[9px] font-bold uppercase text-cyan-200">ENDS IN:</p>
                <div id="countdown" class="text-xl md:text-3xl font-black points">--:--:--</div>
            </div>
        </header>

        <div class="mb-8">
            <p class="text-[10px] font-black text-white/60 mb-3 px-2 italic tracking-widest">HALL OF FAME</p>
            <div class="flex gap-3 overflow-x-auto no-scrollbar pb-2 px-2">
                {records_html or '<p class="text-[10px] opacity-30">Archive empty...</p>'}
            </div>
        </div>

        <div class="w-full">
        """

        for i, p in enumerate(jugadores, 1):
            fb_id = str(p.get('facebook_id', ''))
            nombre = p.get('facebook_name', 'Unknown')
            nombre_upper = nombre.strip().upper()
            bp = p.get('battle_points', 0)
            btls = p.get('total_battle', 0)
            wins = p.get('total_win', 0)
            wr = (wins / btls * 100) if btls > 0 else 0
            pais = p.get('country', '??').lower()
            
            h = MEDALLERO_HISTORICO.get(nombre_upper, {'oro': 0, 'plata': 0, 'bronce': 0})
            badges = ""
            if h['oro'] > 0: badges += f'<span class="badge-mini b-oro">🥇{h["oro"]}</span>'
            if h['plata'] > 0: badges += f'<span class="badge-mini b-plata">🥈{h["plata"]}</span>'
            if h['bronce'] > 0: badges += f'<span class="badge-mini b-bronce">🥉{h["bronce"]}</span>'

            row_class = f"top-{i}" if i <= 3 else "glass"
            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"

            html_content += f"""
                <div class="r-tr {row_class} mb-2 rounded-xl flex flex-col md:flex-row md:items-center p-4 md:px-6 transition-all hover:bg-white/20">
                    <div class="order-3-m md:w-20 text-center">
                        <span class="text-2xl md:text-3xl font-black italic text-slate-400">{icon}</span>
                        <div class="md:hidden points text-white italic font-bold">{bp:,}</div>
                    </div>
                    <div class="order-1-m flex items-center gap-4 flex-1">
                        <div class="relative shrink-0">
                            <img src="https://graph.facebook.com/{fb_id}/picture?type=large" class="w-12 h-12 md:w-16 md:h-16 rounded-full border-2 border-white/40 object-cover" onerror="this.src='https://ui-avatars.com/api/?name={nombre}&background=random';">
                            <img src="https://flagcdn.com/w40/{pais}.png" class="absolute -bottom-1 -right-1 w-6 rounded shadow-lg">
                        </div>
                        <div class="min-w-0">
                            <div class="flex flex-wrap items-center gap-y-1">
                                <h3 class="text-base md:text-xl font-black italic uppercase text-white truncate leading-tight">{nombre}</h3>
                                <div class="flex">{badges}</div>
                            </div>
                            <span class="admin-only-id">UUID_{fb_id[:8]}</span>
                        </div>
                    </div>
                    <div class="order-2-m md:w-64 pt-2 md:pt-0">
                        <div class="flex items-center justify-between md:justify-center gap-6">
                            <div class="text-center"><p class="text-[8px] text-white/50 uppercase font-black">MATCHES</p><p class="text-xs font-bold text-white italic">{btls}</p></div>
                            <div class="text-center"><p class="text-[8px] text-green-400 uppercase font-black">WINS</p><p class="text-xs font-bold text-white italic">{wins}</p></div>
                            <div class="flex-1 max-w-[80px]">
                                <div class="flex justify-between text-[7px] text-white/70 font-black mb-1"><span>WR</span><span class="text-cyan-400">{wr:.0f}%</span></div>
                                <div class="w-full bg-black/40 h-1.5 rounded-full overflow-hidden"><div class="bg-gradient-to-r from-blue-500 to-cyan-400 h-full" style="width: {wr}%"></div></div>
                            </div>
                        </div>
                    </div>
                    <div class="hidden md:block md:w-32 text-right"><div class="points text-2xl font-black italic text-cyan-400">{bp:,}</div></div>
                </div>
            """

        html_content += """
        </div>
    </div>
    <script>
        const currentS = """ + str(ID_SEASON) + """;
        const sel = document.getElementById('seasonSelector');
        let h_opt = document.createElement('option'); h_opt.value='#'; h_opt.innerText='HISTORY'; sel.appendChild(h_opt);
        for(let i = currentS; i >= 1; i--) {
            let opt = document.createElement('option');
            opt.value = i === currentS ? 'index.html' : `Season_${i}.html`;
            opt.innerText = `Season ${i}`;
            if(window.location.href.includes(opt.value)) opt.selected = true;
            sel.appendChild(opt);
        }

        const targetDate = new Date(""" + f'"{FECHA_ISO_CIERRE}"' + """).getTime();
        function updateTimer() {
            const now = new Date().getTime();
            const diff = targetDate - now;
            if (diff < 0) { document.getElementById("countdown").innerHTML = "ENDED"; return; }
            const d = Math.floor(diff / (1000 * 60 * 60 * 24));
            const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const s = Math.floor((diff % (1000 * 60)) / 1000);
            document.getElementById("countdown").innerHTML = `${d}D ${h.toString().padStart(2,'0')}H ${m.toString().padStart(2,'0')}M ${s.toString().padStart(2,'0')}S`;
        }
        setInterval(updateTimer, 1000);
        updateTimer();
    </script>
</body>
</html>
"""
        # --- GUARDADO ---
        # No importa si corre en GitHub o en Windows, se guardará en la carpeta del script.
        ruta_script = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(ruta_script, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
        with open(os.path.join(ruta_script, f"Season_{ID_SEASON}.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"🚀 Ranking actualizado con éxito para la {NOMBRE_SEASON}")

except Exception as e:
    print(f"❌ ERROR: {e}")