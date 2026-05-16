# src/generator/script_generator.py
import os, json, re
from config.settings import GUIONES_DIR, PROVIDERS_TEXTO

os.makedirs(GUIONES_DIR, exist_ok=True)

def _nombre_archivo(tema: str) -> str:
    nombre = tema.lower().strip()
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
    nombre = re.sub(r'\s+', '_', nombre)
    return os.path.join(GUIONES_DIR, f"{nombre}.json")

def ya_existe(tema: str) -> bool:
    return os.path.exists(_nombre_archivo(tema))

def guardar_guion(guion: dict):
    ruta = _nombre_archivo(guion["tema"])
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(guion, f, ensure_ascii=False, indent=2)

def listar_guiones(estado: str = None) -> list:
    guiones = []
    if not os.path.exists(GUIONES_DIR):
        return guiones
    for archivo in os.listdir(GUIONES_DIR):
        if archivo.endswith('.json'):
            ruta = os.path.join(GUIONES_DIR, archivo)
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    g = json.load(f)
                if estado is None or g.get("estado") == estado:
                    guiones.append(g)
            except:
                pass
    return guiones

def _get_client(proveedor: str, api_key: str):
    if proveedor == "gemini":
        from google import genai
        return genai.Client(api_key=api_key)
    elif proveedor == "claude":
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    elif proveedor in ["openai", "deepseek", "qwen"]:
        from openai import OpenAI
        config = PROVIDERS_TEXTO[proveedor]
        kwargs = {"api_key": api_key}
        if "base_url" in config:
            kwargs["base_url"] = config["base_url"]
        return OpenAI(**kwargs)
    raise ValueError(f"Proveedor no soportado: {proveedor}")

def _llamar_api(proveedor: str, api_key: str, prompt: str) -> str:
    config = PROVIDERS_TEXTO[proveedor]
    modelo = config["modelo"]
    client = _get_client(proveedor, api_key)

    if proveedor == "gemini":
        respuesta = client.models.generate_content(model=modelo, contents=prompt)
        return respuesta.text
    elif proveedor == "claude":
        respuesta = client.messages.create(
            model=modelo,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return respuesta.content[0].text
    elif proveedor in ["openai", "deepseek", "qwen"]:
        respuesta = client.chat.completions.create(
            model=modelo,
            messages=[{"role": "user", "content": prompt}]
        )
        return respuesta.choices[0].message.content

def generar_guion(tema: str, duracion: int = 30, estilo: str = "educativo",
                  proveedor: str = "gemini", api_key: str = None) -> dict:

    if ya_existe(tema):
        ruta = _nombre_archivo(tema)
        with open(ruta, 'r', encoding='utf-8') as f:
            guion = json.load(f)
        print(f"⚠️  Ya existe guión para '{tema}', cargando...")
        return guion

    if not api_key:
        from config.settings import ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY, QWEN_API_KEY
        keys = {
            "gemini": GEMINI_API_KEY,
            "claude": ANTHROPIC_API_KEY,
            "openai": OPENAI_API_KEY,
            "deepseek": DEEPSEEK_API_KEY,
            "qwen": QWEN_API_KEY,
        }
        api_key = keys.get(proveedor, "")

    if not api_key:
        raise ValueError(f"No hay API key para {proveedor}.")

    prompt = f"""Eres un experto creador de contenido viral para TikTok y YouTube Shorts.

Crea un guión completo para un video corto con estas especificaciones:
- Tema: {tema}
- Duración: {duracion} segundos aproximadamente
- Estilo: {estilo}
- Idioma: Español
- Formato: Vertical (TikTok/Reels)

Responde ÚNICAMENTE en este formato JSON exacto, sin explicaciones ni texto adicional:

{{
  "titulo": "Título llamativo del video",
  "gancho": "Primera frase impactante para los primeros 3 segundos",
  "guion_completo": "Texto completo que se narrará en voz en off",
  "escenas": [
    {{
      "numero": 1,
      "duracion_segundos": 5,
      "texto_narrado": "Lo que se dice en esta escena",
      "descripcion_visual": "Lo que se ve en pantalla",
      "prompt_imagen": "Prompt en inglés para generar imagen con IA, muy detallado y visual, maximum 100 words"
    }}
  ],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
  "descripcion_youtube": "Descripción optimizada para YouTube",
  "descripcion_tiktok": "Descripción corta para TikTok con emojis"
}}

IMPORTANTE: Máximo 5 escenas. Los prompts de imagen deben ser cortos (máximo 100 palabras en inglés)."""

    texto = _llamar_api(proveedor, api_key, prompt)
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    texto = texto.strip()

    guion = json.loads(texto)
    guion["tema"] = tema
    guion["estado"] = "sin_voz"
    guion["proveedor"] = proveedor
    guardar_guion(guion)
    print(f"💾 Guión guardado: {_nombre_archivo(tema)}")
    return guion

def mostrar_guion(guion: dict):
    print("\n" + "="*60)
    print(f"🎬 TÍTULO: {guion['titulo']}")
    print(f"🎣 GANCHO: {guion['gancho']}")
    print(f"📊 ESTADO: {guion.get('estado', 'desconocido')}")
    print(f"🤖 PROVEEDOR: {guion.get('proveedor', 'desconocido')}")
    print("="*60)
    print(f"\n📝 GUIÓN:\n{guion['guion_completo']}")
    print(f"\n#️⃣  HASHTAGS: {' '.join(guion['hashtags'])}")
    print("="*60)