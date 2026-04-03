"""
🏎️  F1 Explorer — OpenF1 API
Consulta resultados, tiempos y datos de carreras de Fórmula 1.
API gratuita: https://openf1.org  (datos desde 2023, sin autenticación)
"""

import json
import sys
from urllib.request import urlopen
from urllib.error import URLError
from urllib.parse import urlencode
from datetime import datetime

BASE_URL = "https://api.openf1.org/v1"

# ──────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────

def fetch(endpoint: str, params: dict = None) -> list:
    """Llama a la API y devuelve una lista de objetos JSON."""
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url += "?" + urlencode(params, doseq=True)
    try:
        response = urlopen(url, timeout=10)
        return json.loads(response.read().decode("utf-8"))
    except URLError as e:
        print(f"  ❌  Error de red: {e.reason}")
        return []
    except Exception as e:
        print(f"  ❌  Error inesperado: {e}")
        return []


def fmt_lap(ms: float | None) -> str:
    """Convierte milisegundos a formato M:SS.mmm"""
    if ms is None:
        return "–"
    total_s = ms / 1000
    minutes = int(total_s // 60)
    seconds = total_s % 60
    return f"{minutes}:{seconds:06.3f}"


def separator(char="─", width=60):
    print(char * width)


def header(title: str):
    separator("═")
    print(f"  🏎️   {title}")
    separator("═")


# ──────────────────────────────────────────
# Módulos de consulta
# ──────────────────────────────────────────

def listar_grandes_premios():
    """Lista todos los Grandes Premios disponibles."""
    header("Grandes Premios disponibles")
    meetings = fetch("meetings")
    if not meetings:
        print("  Sin datos.")
        return

    # Ordenar por año y número
    meetings.sort(key=lambda m: (m.get("year", 0), m.get("meeting_key", 0)))

    año_actual = None
    for m in meetings:
        año = m.get("year", "?")
        if año != año_actual:
            print(f"\n  📅  Temporada {año}")
            separator("-", 40)
            año_actual = año
        key = m.get("meeting_key", "?")
        nombre = m.get("meeting_name", "?")
        pais = m.get("country_name", "?")
        circuito = m.get("circuit_short_name", "?")
        print(f"    [{key}]  {nombre} — {circuito}, {pais}")

    print()


def resultado_carrera():
    """Muestra el resultado (posiciones finales) de una carrera."""
    header("Resultado de carrera")
    meeting_key = input("  Introduce el meeting_key del GP (o 'latest'): ").strip() or "latest"

    # Buscar la sesión de carrera
    sessions = fetch("sessions", {"meeting_key": meeting_key, "session_name": "Race"})
    if not sessions:
        print("  No se encontró sesión de carrera para ese GP.")
        return

    session = sessions[0]
    session_key = session["session_key"]

    # Obtener nombre del GP desde meetings
    meetings = fetch("meetings", {"meeting_key": meeting_key})
    gp_name = meetings[0].get("meeting_name", "?") if meetings else "?"

    print(f"\n  🏁  {gp_name} — Race  |  {session.get('date_start', '')[:10]}")
    separator()

    # Resultado final de la sesión
    results = fetch("session_result", {"session_key": session_key})
    if not results:
        print("  Sin resultados aún.")
        return

    # Obtener nombres de pilotos
    drivers_data = fetch("drivers", {"session_key": session_key})
    driver_map = {d["driver_number"]: d for d in drivers_data}

    results.sort(key=lambda r: r.get("position") or 999)

    print(f"  {'POS':>4}  {'#':>3}  {'PILOTO':<25}  {'EQUIPO':<22}")
    separator("-", 65)
    for r in results:
        pos = r.get("position")
        num = r.get("driver_number")
        drv = driver_map.get(num, {})
        nombre = drv.get("full_name", f"Piloto #{num}")
        equipo = drv.get("team_name", "–")
        pos_s = str(pos) if pos is not None else "DNF"
        num_s = str(num) if num is not None else "?"
        print(f"  {pos_s:>4}  {num_s:>3}  {nombre:<25}  {equipo:<22}")
    print()


def tiempos_por_vuelta():
    """Muestra tiempos por vuelta de un piloto en una sesión."""
    header("Tiempos por vuelta")
    meeting_key = input("  Introduce el meeting_key del GP (o 'latest'): ").strip() or "latest"

    # Listar sesiones del GP
    sessions = fetch("sessions", {"meeting_key": meeting_key})
    if not sessions:
        print("  No se encontraron sesiones.")
        return

    print(f"\n  Sesiones disponibles para meeting_key={meeting_key}:")
    for s in sessions:
        print(f"    [{s['session_key']}]  {s.get('session_name','?')}  ({s.get('date_start','')[:10]})")

    session_key = input("\n  Introduce el session_key: ").strip()
    if not session_key:
        return

    # Pilotos
    drivers_data = fetch("drivers", {"session_key": session_key})
    if not drivers_data:
        print("  Sin pilotos en esa sesión.")
        return

    print("\n  Pilotos en la sesión:")
    drivers_data.sort(key=lambda d: d.get("driver_number", 0))
    for d in drivers_data:
        print(f"    [{d['driver_number']:>2}]  {d.get('full_name','?'):<25}  {d.get('team_name','?')}")

    driver_num = input("\n  Número de piloto: ").strip()
    if not driver_num:
        return

    laps = fetch("laps", {"session_key": session_key, "driver_number": driver_num})
    if not laps:
        print("  Sin datos de vueltas.")
        return

    laps.sort(key=lambda l: l.get("lap_number", 0))

    # Nombre del piloto
    drv = next((d for d in drivers_data if str(d["driver_number"]) == driver_num), {})
    print(f"\n  🕐  Tiempos de {drv.get('full_name', f'#{driver_num}')} — {drv.get('team_name', '')}")
    separator()
    print(f"  {'VLT':>4}  {'TIEMPO':>12}  {'S1':>10}  {'S2':>10}  {'S3':>10}  {'COMPUESTO':<15}")
    separator("-", 70)

    mejor = None
    for lap in laps:
        t = lap.get("lap_duration")
        if t and (mejor is None or t < mejor):
            mejor = t

    for lap in laps:
        n = lap.get("lap_number", "?")
        t = lap.get("lap_duration")
        s1 = lap.get("duration_sector_1")
        s2 = lap.get("duration_sector_2")
        s3 = lap.get("duration_sector_3")
        comp = lap.get("compound", "–")
        marca = "  ← 🟣 Vuelta rápida" if t == mejor else ""
        print(f"  {n:>4}  {fmt_lap(t * 1000 if t else None):>12}  "
              f"{fmt_lap(s1 * 1000 if s1 else None):>10}  "
              f"{fmt_lap(s2 * 1000 if s2 else None):>10}  "
              f"{fmt_lap(s3 * 1000 if s3 else None):>10}  {comp:<15}{marca}")
    print()


def clasificacion_campeonato():
    """Muestra la clasificación del campeonato de pilotos."""
    header("Clasificación del Campeonato de Pilotos")
    meeting_key = input("  Introduce el meeting_key del GP (o 'latest'): ").strip() or "latest"

    sessions = fetch("sessions", {"meeting_key": meeting_key, "session_name": "Race"})
    if not sessions:
        print("  No se encontró sesión de carrera.")
        return

    session_key = sessions[0]["session_key"]
    standings = fetch("championship_drivers", {"session_key": session_key})
    if not standings:
        print("  Sin datos de campeonato para esa sesión.")
        return

    drivers_data = fetch("drivers", {"session_key": session_key})
    driver_map = {d["driver_number"]: d for d in drivers_data}

    standings.sort(key=lambda s: s.get("position_current") or 999)

    print(f"\n  {'POS':>4}  {'PILOTO':<25}  {'PUNTOS':>8}  {'CAMBIO':>8}")
    separator("-", 55)
    for s in standings:
        pos = s.get("position_current", "?")
        num = s.get("driver_number")
        drv = driver_map.get(num, {})
        nombre = drv.get("full_name", f"#{num}")
        pts = s.get("points_current", 0)
        ganados = pts - s.get("points_start", pts)
        signo = f"+{ganados}" if ganados > 0 else str(ganados)
        print(f"  {pos:>4}  {nombre:<25}  {pts:>8}  {signo:>8}")
    print()


def paradas_en_pits():
    """Muestra las paradas en boxes de una sesión."""
    header("Paradas en Pits")
    meeting_key = input("  Introduce el meeting_key del GP (o 'latest'): ").strip() or "latest"

    sessions = fetch("sessions", {"meeting_key": meeting_key, "session_name": "Race"})
    if not sessions:
        print("  No se encontró sesión de carrera.")
        return

    session_key = sessions[0]["session_key"]
    pits = fetch("pit", {"session_key": session_key})
    if not pits:
        print("  Sin datos de pits.")
        return

    drivers_data = fetch("drivers", {"session_key": session_key})
    driver_map = {d["driver_number"]: d for d in drivers_data}

    pits.sort(key=lambda p: (p.get("lap_number", 0), p.get("driver_number", 0)))

    print(f"\n  {'VLT':>4}  {'PILOTO':<25}  {'PARADA (s)':>12}  {'CARRIL (s)':>12}")
    separator("-", 60)
    for p in pits:
        num = p.get("driver_number")
        drv = driver_map.get(num, {})
        nombre = drv.get("full_name", f"#{num}")
        vlt = p.get("lap_number") or "?"
        stop = p.get("stop_duration")
        lane = p.get("lane_duration")
        stop_s = f"{stop:.2f}s" if isinstance(stop, (int, float)) else "–"
        lane_s = f"{lane:.2f}s" if isinstance(lane, (int, float)) else "–"
        vlt_s = str(vlt)
        print(f"  {vlt_s:>4}  {nombre:<25}  {stop_s:>12}  {lane_s:>12}")
    print()


def clima_en_sesion():
    """Muestra datos meteorológicos durante una sesión."""
    header("Clima durante la sesión")
    meeting_key = input("  Introduce el meeting_key del GP (o 'latest'): ").strip() or "latest"

    sessions = fetch("sessions", {"meeting_key": meeting_key})
    if not sessions:
        print("  No se encontraron sesiones.")
        return

    print("\n  Sesiones disponibles:")
    for s in sessions:
        print(f"    [{s['session_key']}]  {s.get('session_name','?')}  ({s.get('date_start','')[:10]})")

    session_key = input("\n  Introduce el session_key: ").strip()
    if not session_key:
        return

    weather = fetch("weather", {"session_key": session_key})
    if not weather:
        print("  Sin datos meteorológicos.")
        return

    # Mostrar un resumen (primer, último y promedio)
    temps_aire = [w.get("air_temperature") for w in weather if w.get("air_temperature") is not None]
    temps_pista = [w.get("track_temperature") for w in weather if w.get("track_temperature") is not None]
    humedad = [w.get("humidity") for w in weather if w.get("humidity") is not None]
    lluvia = any(w.get("rainfall") for w in weather)

    def avg(lst):
        return sum(lst) / len(lst) if lst else None

    print(f"\n  {'Parámetro':<25}  {'Mín':>8}  {'Prom':>8}  {'Máx':>8}")
    separator("-", 55)
    for label, lst in [("Temp. Aire (°C)", temps_aire), ("Temp. Pista (°C)", temps_pista), ("Humedad (%)", humedad)]:
        if lst:
            print(f"  {label:<25}  {min(lst):>8.1f}  {avg(lst):>8.1f}  {max(lst):>8.1f}")
    print(f"\n  🌧️  Lluvia detectada: {'Sí' if lluvia else 'No'}")
    print()


# ──────────────────────────────────────────
# Menú principal
# ──────────────────────────────────────────

MENU = {
    "1": ("Listar Grandes Premios disponibles", listar_grandes_premios),
    "2": ("Resultado de carrera (posiciones finales)", resultado_carrera),
    "3": ("Tiempos por vuelta de un piloto", tiempos_por_vuelta),
    "4": ("Clasificación del Campeonato de Pilotos", clasificacion_campeonato),
    "5": ("Paradas en Pits de una carrera", paradas_en_pits),
    "6": ("Clima durante una sesión", clima_en_sesion),
    "0": ("Salir", None),
}


def main():
    print()
    separator("═")
    print("  🏎️   F1 EXPLORER  — OpenF1 API (datos desde 2023)")
    print("  🌐  openf1.org  |  Gratuita, sin autenticación")
    separator("═")

    while True:
        print("\n  MENÚ PRINCIPAL\n")
        for key, (label, _) in MENU.items():
            print(f"    [{key}]  {label}")
        print()

        opcion = input("  Elige una opción: ").strip()

        if opcion == "0":
            print("\n  ¡Hasta la próxima vuelta! 🏁\n")
            sys.exit(0)

        if opcion in MENU:
            print()
            MENU[opcion][1]()
        else:
            print("  ⚠️  Opción no válida, intenta de nuevo.")


if __name__ == "__main__":
    main()