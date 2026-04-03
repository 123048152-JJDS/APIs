import requests

BASE_URL = "https://thesimpsonsapi.com/api"

session = requests.Session()


# ── Helper base ───────────────────────────────────────────────────────────────

def _get(path: str, **params) -> dict | None:
    """Realiza un GET y maneja errores de forma centralizada."""
    try:
        response = session.get(f"{BASE_URL}{path}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        print(f"  Error HTTP {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("  Error: no se pudo conectar a la API.")
    except requests.exceptions.Timeout:
        print("  Error: la petición tardó demasiado.")
    return None


# ── Personajes ────────────────────────────────────────────────────────────────

def get_character_by_id(character_id: int) -> dict | None:
    return _get(f"/characters/{character_id}")

def search_characters(name: str, page: int = 1) -> dict | None:
    return _get("/characters", name=name, page=page)

def get_characters(page: int = 1) -> dict | None:
    return _get("/characters", page=page)

def get_all_characters() -> list[dict]:
    all_chars, page = [], 1
    while True:
        data = get_characters(page=page)
        if not data or not data.get("results"):
            break
        all_chars.extend(data["results"])
        print(f"  Página {page} — {len(all_chars)}/{data.get('count', '?')}")
        if not data.get("next"):
            break
        page += 1
    return all_chars

def print_character(c: dict) -> None:
    print(f"\n  ID         : {c.get('id')}")
    print(f"  Nombre     : {c.get('name')}")
    print(f"  Ocupación  : {c.get('occupation') or '—'}")
    print(f"  Estado     : {c.get('status') or '—'}")
    print(f"  Edad       : {c.get('age') or '—'}")
    if c.get("phrases"):
        print(f"  Frases     :")
        for phrase in c["phrases"][:3]:
            print(f'    "{phrase}"')


# ── Episodios ─────────────────────────────────────────────────────────────────

def get_episode_by_id(episode_id: int) -> dict | None:
    return _get(f"/episodes/{episode_id}")

def get_episodes(page: int = 1, season: int | None = None) -> dict | None:
    params = {"page": page}
    if season:
        params["season"] = season
    return _get("/episodes", **params)

def search_episodes(title: str, page: int = 1) -> dict | None:
    return _get("/episodes", title=title, page=page)

def print_episode(e: dict) -> None:
    print(f"\n  ID         : {e.get('id')}")
    print(f"  Título     : {e.get('title') or '—'}")
    print(f"  Temporada  : {e.get('season') or '—'}")
    print(f"  Episodio   : {e.get('episode_in_season') or '—'}")
    print(f"  Fecha aire : {e.get('air_date') or '—'}")
    if e.get("synopsis"):
        sinopsis = e["synopsis"]
        print(f"  Sinopsis   : {sinopsis[:120]}{'...' if len(sinopsis) > 120 else ''}")


# ── Ubicaciones ───────────────────────────────────────────────────────────────

def get_location_by_id(location_id: int) -> dict | None:
    return _get(f"/locations/{location_id}")

def get_locations(page: int = 1) -> dict | None:
    return _get("/locations", page=page)

def search_locations(name: str, page: int = 1) -> dict | None:
    return _get("/locations", name=name, page=page)

def print_location(loc: dict) -> None:
    print(f"\n  ID         : {loc.get('id')}")
    print(f"  Nombre     : {loc.get('name') or '—'}")
    if loc.get("description"):
        desc = loc["description"]
        print(f"  Descripción: {desc[:120]}{'...' if len(desc) > 120 else ''}")
    if loc.get("image_path"):
        print(f"  Imagen     : https://cdn.thesimpsonsapi.com/500{loc['image_path']}")
        img = "https://cdn.thesimpsonsapi.com/500" + loc["image_path"]
        open_image = input("  ¿Quieres abrir la imagen? (s/n): ").strip().lower()
        if open_image == "s":
            import webbrowser
            webbrowser.open(img)
        
    if loc.get("town"):
        print(f"  Ciudad     : {loc['town']}")
    if loc.get("use"):
        print(f"  Uso        : {loc['use']}")

# ── Menú CLI ──────────────────────────────────────────────────────────────────

def menu_characters() -> None:
    opciones = {
        "1": "Buscar por ID",
        "2": "Buscar por nombre",
        "3": "Listar (paginado)",
        "4": "Descargar todos",
        "0": "Volver",
    }
    while True:
        print("\n  ── PERSONAJES ──────────────────────")
        for k, v in opciones.items():
            print(f"  [{k}] {v}")

        op = input("  Opción: ").strip()

        if op == "0":
            break
        elif op == "1":
            try:
                cid = int(input("  ID: "))
                char = get_character_by_id(cid)
                if char:
                    print_character(char)
            except ValueError:
                print("  El ID debe ser un número.")
        elif op == "2":
            name = input("  Nombre: ").strip()
            if not name:
                continue
            data = search_characters(name)
            if data and data.get("results"):
                print(f"\n  Encontrados: {data['count']}")
                for c in data["results"]:
                    print_character(c)
            else:
                print("  Sin resultados.")
        elif op == "3":
            try:
                page = int(input("  Página (default 1): ") or "1")
                data = get_characters(page=page)
                if data and data.get("results"):
                    print(f"\n  Página {page} — Total: {data['count']}")
                    for c in data["results"]:
                        print(f"  [{c['id']:4}] {c['name']}")
                else:
                    print("  Sin resultados.")
            except ValueError:
                print("  Número de página inválido.")
        elif op == "4":
            print("\n  Descargando todos los personajes...")
            chars = get_all_characters()
            print(f"\n  Total: {len(chars)}")
            print(f"  Primero: {chars[0]['name']}")
            print(f"  Último : {chars[-1]['name']}")


def menu_episodes() -> None:
    opciones = {
        "1": "Buscar por ID",
        "2": "Buscar por título",
        "3": "Listar (paginado)",
        "4": "Filtrar por temporada",
        "0": "Volver",
    }
    while True:
        print("\n  ── EPISODIOS ───────────────────────")
        for k, v in opciones.items():
            print(f"  [{k}] {v}")

        op = input("  Opción: ").strip()

        if op == "0":
            break
        elif op == "1":
            try:
                eid = int(input("  ID: "))
                ep = get_episode_by_id(eid)
                if ep:
                    print_episode(ep)
            except ValueError:
                print("  El ID debe ser un número.")
        elif op == "2":
            title = input("  Título: ").strip()
            if not title:
                continue
            data = search_episodes(title)
            if data and data.get("results"):
                print(f"\n  Encontrados: {data['count']}")
                for ep in data["results"]:
                    print_episode(ep)
            else:
                print("  Sin resultados.")
        elif op == "3":
            try:
                page = int(input("  Página (default 1): ") or "1")
                data = get_episodes(page=page)
                if data and data.get("results"):
                    print(f"\n  Página {page} — Total: {data['count']}")
                    for ep in data["results"]:
                        s = str(ep.get("season", "?")).zfill(2)
                        e = str(ep.get("episode_in_season", "?")).zfill(2)
                        print(f"  [{ep['id']:4}] S{s}E{e} {ep.get('title', '—')}")
                else:
                    print("  Sin resultados.")
            except ValueError:
                print("  Número de página inválido.")
        elif op == "4":
            try:
                season = int(input("  Número de temporada: "))
                data = get_episodes(season=season)
                if data and data.get("results"):
                    print(f"\n  Temporada {season} — {data['count']} episodios")
                    for ep in data["results"]:
                        e = str(ep.get("episode_in_season", "?")).zfill(2)
                        print(f"  [E{e}] {ep.get('title', '—')}")
                else:
                    print("  Sin resultados para esa temporada.")
            except ValueError:
                print("  Ingresa un número de temporada válido.")

def menu_locations() -> None:
    opciones = {
        "1": "Buscar por ID",
        "2": "Buscar por nombre",
        "3": "Listar (paginado)",
        "0": "Volver",
    }
    while True:
        print("\n  ── UBICACIONES ─────────────────────")
        print(f"\tPáginas totales: {data['pages']}" if (data := get_locations()) else "  No se pudo obtener el total de páginas.")
        print(f"\tTotal de ubicaciones: {data['count']}" if data else "  No se pudo obtener el total de ubicaciones.")

        for k, v in opciones.items():
            print(f"  [{k}] {v}")

        op = input("  Opción: ").strip()

        if op == "0":
            break
        elif op == "1":
            try:
                lid = int(input("  ID: "))
                loc = get_location_by_id(lid)
                if loc:
                    print_location(loc)
                    
            except ValueError:
                print("  El ID debe ser un número.")
        elif op == "2":
            name = input("  Nombre: ").strip()
            if not name:
                continue
            data = search_locations(name)
            if data and data.get("results"):
                print(f"\n  Encontrados: {data['count']}")
                for loc in data["results"]:
                    print_location(loc)
            else:
                print("  Sin resultados.")
        elif op == "3":
            try:
                print("  Cargando ubicaciones...")
                page = int(input("  Página (default 1): ") or "1")
                data = get_locations(page=page)
                if data and data.get("results"):
                    print(f"\n  Página {page} — Total: {data['count']}")
                    for loc in data["results"]:
                        print(f"  [{loc['id']:4}] {loc.get('name', '—')}")
                else:
                    print("  Sin resultados.")
            except ValueError:
                print("  Número de página inválido.")


def menu() -> None:
    opciones = {
        "1": "Personajes",
        "2": "Episodios",
        "3": "Ubicaciones",
        "4": "Salir",
    }
    while True:
        print("\n" + "═" * 40)
        print("   THE SIMPSONS API — EXPLORADOR")
        print("═" * 40)
        for k, v in opciones.items():
            print(f"  [{k}] {v}")
        print("═" * 40)

        op = input("Elige una opción: ").strip()

        if op == "1":
            menu_characters()
        elif op == "2":
            menu_episodes()
        elif op == "3":
            menu_locations()
        elif op == "4":
            print("\n  ¡Hasta luego! D'oh!\n")
            break
        else:
            print("  Opción no válida.")


if __name__ == "__main__":
    menu()
