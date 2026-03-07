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
    # AJUSTE: Ahora termina exactamente a las 11:00 PM (23:00) del domingo
    fecha_final_esta_season = fecha_inicio_esta_season + timedelta(days=13, hours=23, minutes=0)
    return id_actual, fecha_final_esta_season

ID_SEASON, FECHA_CIERRE = calcular_info_season()
NOMBRE_SEASON = f"Season {ID_SEASON}"
FECHA_ISO_CIERRE = FECHA_CIERRE.strftime("%Y-%m-%dT%H:%M:%S")

# ==========================================
# 2. ESCÁNER HISTÓRICO (RÉCORDS Y MEDALLERO)
# ==========================================
def escanear_historial_completo():
    stats_medallas = {}
    records_puntos = []
    
    for i in range(1, ID_SEASON): 
        archivo = f"Season_{i}.html"
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    contenido = f.read()
                    nombres = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', contenido)
                    puntos_raw = re.findall(r'class="(?:points|pts)[^>]*>([\d,.]+)</', contenido)
                    paises = re.findall(r'flagcdn\.com/w20/(..)\.png', contenido)
                    
                    for idx, nombre in enumerate(nombres[:3]):
                        nom_limpio = nombre.strip().upper()
                        pais_code = paises[idx] if idx < len(paises) else "un"
                        
                        if nom_limpio not in stats_medallas:
                            stats_medallas[nom_limpio] = {'oro': 0, 'plata': 0, 'bronce': 0, 'total': 0, 'pais': pais_code, 'display_name': nombre.strip()}
                        
                        if idx == 0: stats_medallas[nom_limpio]['oro'] += 1
                        elif idx == 1: stats_medallas[nom_limpio]['plata'] += 1
                        elif idx == 2: stats_medallas[nom_limpio]['bronce'] += 1
                        stats_medallas[nom_limpio]['total'] += 1
                    
                    for idx, p_str in enumerate(puntos_raw):
                        if idx < len(nombres):
                            val = int(p_str.replace(',', '').replace('.', ''))
                            pais_code = paises[idx] if idx < len(paises) else "un"
                            records_puntos.append({'pts': val, 'nom': nombres[idx].strip(), 's': i, 'pais': pais_code})
            except: continue
            
    records_puntos.sort(key=lambda x: x['pts'], reverse=True)
    ranking_medallas = list(stats_medallas.values())
    ranking_medallas.sort(key=lambda x: (x['total'], x['oro'], x['plata']), reverse=True)
    
    return stats_medallas, records_puntos[:5], ranking_medallas[:5]

MEDALLERO_DICT, TOP_5_RECORDS, TOP_5_DECORATED = escanear_historial_completo()

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

        # HTML: Récords Históricos
        records_html = ""
        colores_r = ["#ffd700", "#e5e5e5", "#cd7f32", "#4ade80", "#22d3ee"]
        for idx, rec in enumerate(TOP_5_RECORDS):
            c = colores_r[idx] if idx < len(colores_r) else "#ffffff"
            records_html += f"""
            <div class="flex-none bg-black/40 backdrop-blur-md px-4 py-3 rounded-xl border-l-4 shadow-lg" style="border-color: {c}; min-width: 150px;">
                <div class="flex justify-between items-start mb-1">
                    <p class="text-[8px] font-black text-white/40 uppercase">S-{rec['s']} RECORD</p>
                    <img src="https://flagcdn.com/w20/{rec['pais']}.png" class="w-3 opacity-80">
                </div>
                <p class="text-xs font-black italic uppercase truncate">{rec['nom']}</p>
                <p class="points text-sm font-black text-cyan-400 leading-tight">{rec['pts']:,}</p>
            </div>"""

        # HTML: Seasons Ganadas
        decorated_html = ""
        for idx, dec in enumerate(TOP_5_DECORATED):
            c = colores_r[idx] if idx < len(colores_r) else "#ffffff"
            decorated_html += f"""
            <div class="flex-none bg-black/40 backdrop-blur-md px-4 py-3 rounded-xl border-l-4 shadow-lg" style="border-color: {c}; min-width: 160px;">
                <div class="flex items-center gap-2 mb-1 border-b border-white/10 pb-1">
                    <img src="https://flagcdn.com/w20/{dec['pais']}.png" class="w-3">
                    <p class="text-xs font-black italic uppercase truncate">{dec['display_name']}</p>
                </div>
                <div class="flex gap-2">
                    <span class="text-[10px] font-bold text-yellow-400">🥇{dec['oro']}</span>
                    <span class="text-[10px] font-bold text-gray-300">🥈{dec['plata']}</span>
                    <span class="text-[10px] font-bold text-orange-400">🥉{dec['bronce']}</span>
                </div>
                <p class="text-[7px] font-black text-cyan-200 mt-1 uppercase tracking-tighter">{dec['total']} TOTAL PODIUMS</p>
            </div>"""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Ranking Leaderboard | {NOMBRE_SEASON}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;700;900&display=swap');
        body {{ background: linear-gradient(180deg, #0f172a 0%, #1e293b 40%, #334155 100%); background-attachment: fixed; color: #ffffff; font-family: 'Inter', sans-serif; min-height: 100vh; }}
        .points {{ font-family: 'Orbitron', sans-serif; text-shadow: 0 0 15px rgba(34, 211, 238, 0.4); }}
        .glass {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5); }}
        .glass:hover {{ background: rgba(255, 255, 255, 0.08); border-color: rgba(255,255,255,0.2); }}
        .badge-mini {{ font-size: 9px; font-weight: 900; padding: 2px 6px; border-radius: 6px; margin-left: 4px; display: inline-flex; align-items: center; gap: 2px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
        .b-oro {{ background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; }}
        .b-plata {{ background: linear-gradient(135deg, #e5e5e5, #a3a3a3); color: #000; }}
        .b-bronce {{ background: linear-gradient(135deg, #cd7f32, #8b4513); color: #fff; }}
        .top-1 {{ background: linear-gradient(90deg, rgba(255, 215, 0, 0.15) 0%, rgba(255,255,255,0.05) 100%) !important; border-left: 4px solid #ffd700 !important; }}
        .no-scrollbar::-webkit-scrollbar {{ display: none; }}
        .no-scrollbar {{ -ms-overflow-style: none; scrollbar-width: none; }}
    </style>
</head>
<body class="p-2 md:p-10">
    <div class="max-w-4xl mx-auto">
        <header class="flex justify-between items-end mb-8 px-2">
            <div>
                <p class="text-[10px] font-black uppercase tracking-widest text-cyan-400">Ranking Leaderboard</p>
                <div class="flex items-center gap-3">
                    <h1 class="text-4xl md:text-6xl font-black italic uppercase tracking-tighter">S-{ID_SEASON}</h1>
                    <select id="seasonSelector" class="bg-white/10 border-none text-[10px] rounded-lg px-2 py-1 text-white focus:ring-2 focus:ring-cyan-500 transition-all outline-none" onchange="if(this.value!='#') window.location.href=this.value"></select>
                </div>
            </div>
            <div class="text-right glass p-4 rounded-3xl border-t border-white/10">
                <p class="text-[9px] font-black uppercase text-cyan-400 tracking-widest mb-1">ENDS IN:</p>
                <div id="countdown" class="text-xl md:text-3xl font-black points tracking-tight text-white">--:--:--</div>
            </div>
        </header>

        <div class="space-y-8 mb-10 px-2">
            <div>
                <p class="text-[10px] font-black text-white/40 mb-3 italic tracking-widest uppercase">Hall of Fame (Best Scores)</p>
                <div class="flex gap-4 overflow-x-auto no-scrollbar pb-4">
                    {records_html or '<p class="text-[10px] opacity-30">No records yet...</p>'}
                </div>
            </div>
            <div>
                <p class="text-[10px] font-black text-white/40 mb-3 italic tracking-widest uppercase">Seasons Ganadas (Top 5)</p>
                <div class="flex gap-4 overflow-x-auto no-scrollbar pb-4">
                    {decorated_html or '<p class="text-[10px] opacity-30">No medals yet...</p>'}
                </div>
            </div>
        </div>

        <div class="w-full space-y-3">
        """

        for i, p in enumerate(jugadores, 1):
            nombre = p.get('facebook_name', 'Unknown')
            nombre_upper = nombre.strip().upper()
            bp = p.get('battle_points', 0)
            btls = p.get('total_battle', 0)
            wins = p.get('total_win', 0)
            wr = (wins / btls * 100) if btls > 0 else 0
            pais = p.get('country', '??').lower()
            
            h = MEDALLERO_DICT.get(nombre_upper, {'oro': 0, 'plata': 0, 'bronce': 0})
            badges = ""
            if h['oro'] > 0: badges += f'<span class="badge-mini b-oro">🥇 {h["oro"]}</span>'
            if h['plata'] > 0: badges += f'<span class="badge-mini b-plata">🥈 {h["plata"]}</span>'
            if h['bronce'] > 0: badges += f'<span class="badge-mini b-bronce">🥉 {h["bronce"]}</span>'

            row_class = "top-1" if i == 1 else "glass"
            rank_color = "text-yellow-400" if i==1 else "text-slate-300" if i==2 else "text-orange-400" if i==3 else "text-white/20"
            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"

            html_content += f"""
            <div class="{row_class} rounded-2xl flex flex-col md:flex-row items-center p-4 md:p-5 transition-all group border border-white/5">
                <div class="md:w-16 text-center text-2xl font-black italic {rank_color} mb-2 md:mb-0">{icon}</div>
                <div class="flex items-center gap-4 flex-1 w-full border-b md:border-b-0 md:border-r border-white/10 pb-3 md:pb-0">
                    <div class="relative">
                        <img src="https://graph.facebook.com/{p.get('facebook_id')}/picture?type=large" class="w-14 h-14 md:w-16 md:h-16 rounded-full border-2 border-white/20 object-cover shadow-lg group-hover:scale-105 transition-transform" onerror="this.src='https://ui-avatars.com/api/?name={nombre}&background=random';">
                        <img src="https://flagcdn.com/w40/{pais}.png" class="absolute -bottom-1 -right-1 w-6 h-4 rounded shadow-md border border-black/20">
                    </div>
                    <div class="min-w-0">
                        <h3 class="text-lg md:text-xl font-black italic uppercase truncate text-white group-hover:text-cyan-400 transition-colors">{nombre}</h3>
                        <div class="flex mt-1 flex-wrap gap-y-1">{badges}</div>
                    </div>
                </div>
                <div class="md:pl-6 md:w-[450px] flex flex-col md:flex-row items-center gap-6 w-full mt-4 md:mt-0">
                    <div class="flex gap-6 text-center shrink-0">
                        <div><p class="text-[8px] text-white/30 uppercase font-black tracking-widest">BATTLES</p><p class="text-sm font-black">{btls}</p></div>
                        <div><p class="text-[8px] text-green-400 uppercase font-black tracking-widest">WINS</p><p class="text-sm font-black text-green-400">{wins}</p></div>
                    </div>
                    <div class="flex-1 w-full max-w-[120px]">
                        <div class="flex justify-between text-[8px] font-black mb-1.5"><span class="text-white/40 uppercase">WINRATE</span><span class="text-cyan-400">{wr:.1f}%</span></div>
                        <div class="w-full bg-black/40 h-2 rounded-full overflow-hidden p-[1px]">
                            <div class="bg-gradient-to-r from-cyan-500 to-blue-600 h-full rounded-full shadow-[0_0_8px_rgba(6,182,212,0.5)]" style="width: {wr}%"></div>
                        </div>
                    </div>
                    <div class="text-right shrink-0">
                        <p class="points text-2xl md:text-3xl font-black italic text-white leading-none tracking-tighter">{bp:,}</p>
                        <p class="text-[7px] font-bold text-cyan-400 uppercase tracking-widest mt-1">BATTLE POINTS</p>
                    </div>
                </div>
            </div>"""

        html_content += """
        </div>
    </div>
    <script>
        const currentS = """ + str(ID_SEASON) + """;
        const sel = document.getElementById('seasonSelector');
        let h_opt = document.createElement('option'); h_opt.value='#'; h_opt.innerText='SELECT SEASON'; sel.appendChild(h_opt);
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
