import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.dragonball-api.com/api"

session = requests.Session()
session.verify = False  # ✅ Desactiva verificación SSL

# Reintentos automáticos ante fallos de red
retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

def _get(path: str, **params) -> dict | None:
    try:
        response = session.get(f"{BASE_URL}{path}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return None

# Personajes
def get_character(id: int) -> dict | None:
    return _get(f"/characters/{id}")

def search_characters(name: str) -> list[dict] | None:
    data = _get("/characters", name=name)
    if data and "items" in data:          # ✅ FIX: extraer lista del objeto paginado
        return data["items"]
    return None

def get_all_characters() -> list[dict] | None:
    data = _get("/characters")
    if data and "items" in data:          # ✅ FIX: extraer lista del objeto paginado
        return data["items"]
    return None

def print_character(char: dict):
    """Imprime los datos de un personaje individual."""
    desc = char.get('description', '')
    print(f"\n{'='*50}")
    print(f"ID          :   {char['id']}")
    print(f"NAME        :   {char['name']}")
    print(f"KI          :   {char['ki']}")
    print(f"MAXKI       :   {char['maxKi']}")
    print(f"RACE        :   {char['race']}")
    print(f"GENDER      :   {char['gender']}")
    print(f"DESCRIPCION :   {desc[:120]}{'...' if len(desc) > 120 else ''}")
    print(f"IMAGE       :   {char['image']}")
    print(f"AFFILIATION :   {char['affiliation']}")
    print(f"DELETED AT  :   {char['deletedAt']}")

    open_image = input("¿Quieres abrir la imagen? (s/n): ").strip().lower()
    if open_image == "s":
        import webbrowser
        webbrowser.open(char['image'])

def print_all_characters():
    characters = get_all_characters()
    if not characters:
        print("No se pudieron obtener los personajes.")
        return
    for char in characters:
        print_character(char)

def main():
    while True:
        print("\n--- Menú de Dragon Ball API ---")
        print("1. Buscar personaje por ID")
        print("2. Buscar personajes por nombre")
        print("3. Listar todos los personajes")
        print("4. Salir")

        choice = input("Selecciona una opción: ").strip()

        if choice == "1":
            try:
                print("\n--- Buscar Personaje por ID ---")
                char_id = int(input("Ingresa el ID del personaje: ").strip())
                character = get_character(char_id)
                if character:                 # ✅ FIX: ahora sí se imprime
                    print_character(character)
                else:
                    print("  Personaje no encontrado.")
            except ValueError:
                print("  El ID debe ser un número.")

        elif choice == "2":                   # ✅ FIX: opción 2 implementada
            print("\n--- Buscar Personaje por Nombre ---")
            name = input("Ingresa el nombre: ").strip()
            results = search_characters(name)
            if results:
                for char in results:
                    print_character(char)
            else:
                print("  No se encontraron personajes.")

        elif choice == "3":                   # ✅ FIX: opción 3 implementada
            print("\n--- Todos los Personajes ---")
            print_all_characters()

        elif choice == "4":                   # ✅ FIX: opción 4 implementada
            print("  ¡Hasta luego!")
            break

        else:
            print("  Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()