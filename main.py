import requests
import json
import os
import re
from datetime import datetime, timedelta

# ==========================================
# 0. CONFIGURACIÓN DE SEGURIDAD
# ==========================================
TOKEN_API = os.getenv("MAGIC_TOKEN", "Mn1iiAAAAB1UI-aNNnM-7833")

# ==========================================
# 1. CONFIGURACIÓN DE SEASON
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
# 2. ESCÁNER HISTÓRICO (SOLO SEASONS PASADAS)
# ==========================================
def escanear_historial_cerrado():
    stats_medallas = {}
    records_puntos = []
    
    # SOLO escanea hasta ID_SEASON - 1 (Excluye la actual del Hall of Fame)
    for i in range(1, ID_SEASON): 
        archivo = f"Season_{i}.html"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    contenido = f.read()
                    nombres = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', contenido)
                    puntos_raw = re.findall(r'class="(?:points|pts)[^>]*>([\d,.]+)</', contenido)
                    
                    # Medallas solo de temporadas pasadas
                    for idx, nombre in enumerate(nombres[:3]):
                        nom_limpio = nombre.strip().upper()
                        if nom_limpio not in stats_medallas:
                            stats_medallas[nom_limpio] = {'oro': 0, 'plata': 0, 'bronce': 0}
                        if idx == 0: stats_medallas[nom_limpio]['oro'] += 1
                        elif idx == 1: stats_medallas[nom_limpio]['plata'] += 1
                        elif idx == 2: stats_medallas[nom_limpio]['bronce'] += 1
                    
                    # Récords solo de temporadas pasadas
                    for idx, p_str in enumerate(puntos_raw):
                        if idx < len(nombres):
                            val = int(p_str.replace(',', '').replace('.', ''))
                            records_puntos.append({'pts': val, 'nom': nombres[idx].strip(), 's': i})
            except: continue
            
    records_puntos.sort(key=lambda x: x['pts'], reverse=True)
    return stats_medallas, records_puntos[:5]

MEDALLERO_HISTORICO, TOP_5_RECORDS = escanear_historial_cerrado()

# ==========================================
# 3. API Y GENERACIÓN DE HTML
# ==========================================
url = "https://ranking.amanotes.net/api/top"
headers = {"accesskey": TOKEN_API, "Content-Type": "application/x-www-form-urlencoded"}
payload = {"accessKey": TOKEN_API, "version": "13.022.001"}

try:
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        jugadores = data if isinstance(data, list) else data.get('ranking', data.get('data', []))

        if os.path.exists("blacklist.json"):
            with open("blacklist.json", "r") as f:
                bl = json.load(f)
                jugadores = [j for j in jugadores if f"UUID_{str(j.get('facebook_id'))[:8]}" not in bl]

        jugadores.sort(key=lambda x: x.get('battle_points', 0), reverse=True)

        records_html = ""
        for idx, rec in enumerate(TOP_5_RECORDS):
            records_html += f"""
            <div class="flex-none glass px-4 py-2 rounded-xl border-b-2 border-white/10">
                <p class="text-[7px] font-bold text-cyan-300 uppercase tracking-tighter"># {idx+1} RECORD (S-{rec['s']})</p>
                <p class="text-xs font-black italic uppercase">{rec['nom']}</p>
                <p class="points text-sm leading-none">{rec['pts']:,}</p>
            </div>"""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Magic Ranking | {NOMBRE_SEASON}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;700;900&display=swap');
        body {{ background: linear-gradient(180deg, #00c6ff 0%, #0072ff 40%, #bc4e9c 100%); background-attachment: fixed; color: #ffffff; font-family: 'Inter', sans-serif; min-height: 100vh; }}
        .points {{ font-family: 'Orbitron', sans-serif; text-shadow: 0 0 10px rgba(0, 210, 255, 0.7); }}
        .glass {{ background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.15); }}
        .badge-mini {{ font-size: 9px; font-weight: 900; padding: 1px 5px; border-radius: 4px; margin-left: 4px; display: inline-flex; align-items: center; gap: 2px; }}
        .b-oro {{ background: #ffd700; color: #000; }}
        .b-plata {{ background: #e5e5e5; color: #000; }}
        .b-bronce {{ background: #cd7f32; color: #fff; }}
        .admin-only-id {{ display: none; }}
        .top-1 {{ background: linear-gradient(90deg, rgba(255, 215, 0, 0.25) 0%, rgba(255,255,255,0.1) 100%) !important; border-left: 4px solid #ffd700; }}
        .no-scrollbar::-webkit-scrollbar {{ display: none; }}
    </style>
</head>
<body class="p-2 md:p-10">
    <div class="max-w-4xl mx-auto">
        <header class="flex justify-between items-end mb-6 px-2">
            <div>
                <p class="text-[10px] font-black uppercase tracking-widest text-cyan-200">MAGIC LEADERBOARD</p>
                <div class="flex items-center gap-3">
                    <h1 class="text-4xl md:text-6xl font-black italic uppercase italic">S-{ID_SEASON}</h1>
                    <select id="seasonSelector" class="bg-black/40 border-none text-[10px] rounded text-white" onchange="if(this.value!='#') window.location.href=this.value"></select>
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
                {records_html or '<p class="text-[10px] opacity-30">No historical records yet...</p>'}
            </div>
        </div>

        <div class="w-full space-y-2">
        """

        for i, p in enumerate(jugadores, 1):
            nombre = p.get('facebook_name', 'Unknown')
            nombre_upper = nombre.strip().upper()
            bp = p.get('battle_points', 0)
            btls = p.get('total_battle', 0)
            wins = p.get('total_win', 0)
            wr = (wins / btls * 100) if btls > 0 else 0
            pais = p.get('country', '??').lower()
            
            # Solo muestra copas si las ganó en seasons pasadas
            h = MEDALLERO_HISTORICO.get(nombre_upper, {'oro': 0, 'plata': 0, 'bronce': 0})
            badges = ""
            if h['oro'] > 0: badges += f'<span class="badge-mini b-oro">🥇{h["oro"]}</span>'
            if h['plata'] > 0: badges += f'<span class="badge-mini b-plata">🥈{h["plata"]}</span>'
            if h['bronce'] > 0: badges += f'<span class="badge-mini b-bronce">🥉{h["bronce"]}</span>'

            row_class = f"top-{i}" if i == 1 else "glass"
            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"

            html_content += f"""
            <div class="{row_class} rounded-xl flex flex-col md:flex-row items-center p-4 transition-all">
                <div class="md:w-20 text-center text-2xl font-black italic text-white/40">{icon}</div>
                <div class="flex items-center gap-4 flex-1 w-full">
                    <img src="https://graph.facebook.com/{p.get('facebook_id')}/picture?type=large" class="w-12 h-12 md:w-16 md:h-16 rounded-full border-2 border-white/40 object-cover" onerror="this.src='https://ui-avatars.com/api/?name={nombre}';">
                    <div class="min-w-0">
                        <div class="flex items-center gap-2">
                            <h3 class="text-base md:text-xl font-black italic uppercase truncate">{nombre}</h3>
                            <img src="https://flagcdn.com/w20/{pais}.png" class="w-5 rounded-sm">
                        </div>
                        <div class="flex">{badges}</div>
                    </div>
                </div>
                <div class="md:w-64 flex justify-between md:justify-center gap-6 w-full mt-2 md:mt-0">
                    <div class="text-center"><p class="text-[8px] text-white/50 uppercase font-black">MATCHES</p><p class="text-xs font-bold">{btls}</p></div>
                    <div class="text-center"><p class="text-[8px] text-green-400 uppercase font-black">WINS</p><p class="text-xs font-bold">{wins}</p></div>
                    <div class="text-right flex-1 md:flex-none">
                        <p class="text-[8px] text-cyan-300 uppercase font-black">SCORE</p>
                        <p class="points text-xl md:text-2xl font-black italic text-cyan-400">{bp:,}</p>
                    </div>
                </div>
            </div>"""

        html_content += """
        </div>
    </div>
    <script>
        const currentS = """ + str(ID_SEASON) + """;
        const sel = document.getElementById('seasonSelector');
        let h_opt = document.createElement('option'); h_opt.value='#'; h_opt.innerText='HISTORY'; sel.appendChild(h_opt);
        for(let i = currentS; i >= 180; i--) {
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
            if (diff < 0) { document.getElementById("countdown").innerHTML = "CLOSED"; return; }
            const d = Math.floor(diff / (1000 * 60 * 60 * 24));
            const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const s = Math.floor((diff % (1000 * 60)) / 1000);
            document.getElementById("countdown").innerHTML = `${d}D ${h.toString().padStart(2,'0')}H ${m.toString().padStart(2,'0')}M ${s.toString().padStart(2,'0')}S`;
        }
        setInterval(updateTimer, 1000); updateTimer();
    </script>
</body>
</html>"""

        with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
        with open(f"Season_{ID_SEASON}.html", "w", encoding="utf-8") as f: f.write(html_content)

except Exception as e: print(f"Error: {e}")
s
