# src/editor/video_editor.py
import os, requests, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from config.settings import IMAGES_DIR, OUTPUT_DIR, VIDEO_WIDTH, VIDEO_HEIGHT
from src.generator.script_generator import guardar_guion

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def descargar_imagen(prompt: str, numero: int, tema: str) -> str:
    nombre = tema.lower().replace(" ", "_")
    nombre = ''.join(c for c in nombre if c.isalnum() or c == '_')
    ruta = os.path.join(IMAGES_DIR, f"{nombre}_escena_{numero}.png")

    if os.path.exists(ruta):
        print(f"  📁 Imagen {numero} ya existe, reutilizando...")
        return ruta

    # Prompt más corto = más rápido en Pollinations
    prompt_corto = prompt[:200]
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt_corto)}?width={VIDEO_WIDTH}&height={VIDEO_HEIGHT}&nologo=true&seed={numero}"

    print(f"  🖼️  Generando imagen {numero}...")

    for intento in range(3):
        try:
            respuesta = requests.get(url, timeout=45)
            if respuesta.status_code == 200:
                with open(ruta, 'wb') as f:
                    f.write(respuesta.content)
                print(f"  ✅ Imagen {numero} guardada")
                return ruta
        except Exception:
            print(f"  ⚠️  Intento {intento+1}/3 imagen {numero}, reintentando...")
            time.sleep(3)

    print(f"  ❌ Falló imagen {numero}, usando fallback")
    return crear_imagen_fallback(prompt[:50], numero, tema)

def crear_imagen_fallback(texto: str, numero: int, tema: str) -> str:
    nombre = tema.lower().replace(" ", "_")
    nombre = ''.join(c for c in nombre if c.isalnum() or c == '_')
    ruta = os.path.join(IMAGES_DIR, f"{nombre}_escena_{numero}.png")
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(10, 10, 30))
    draw = ImageDraw.Draw(img)
    draw.text((VIDEO_WIDTH//2, VIDEO_HEIGHT//2), texto[:50], fill=(0, 255, 65), anchor="mm")
    img.save(ruta)
    return ruta

def agregar_subtitulo(ruta_imagen: str, texto: str, ruta_salida: str) -> str:
    img = Image.open(ruta_imagen).convert("RGB")
    img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT))

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_overlay.rectangle(
        [(0, VIDEO_HEIGHT - 250), (VIDEO_WIDTH, VIDEO_HEIGHT)],
        fill=(0, 0, 0, 180)
    )
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        font = ImageFont.load_default()

    palabras = texto.split()
    lineas = []
    linea_actual = ""
    for palabra in palabras:
        if len(linea_actual + " " + palabra) < 35:
            linea_actual += " " + palabra if linea_actual else palabra
        else:
            lineas.append(linea_actual)
            linea_actual = palabra
    if linea_actual:
        lineas.append(linea_actual)

    y = VIDEO_HEIGHT - 220
    for linea in lineas[:3]:
        draw.text((VIDEO_WIDTH//2, y), linea, font=font, fill="white", anchor="mm",
                  stroke_width=2, stroke_fill="black")
        y += 55

    img.save(ruta)
    return ruta_salida

def generar_video(guion: dict) -> str:
    tema = guion["tema"]
    nombre = tema.lower().replace(" ", "_")
    nombre = ''.join(c for c in nombre if c.isalnum() or c == '_')

    print(f"\n🎬 Generando video: {guion['titulo']}")
    print("="*60)

    audio_path = guion.get("audio")
    if not audio_path or not os.path.exists(audio_path):
        print("❌ No se encontró el audio.")
        return None

    # Limitar a máximo 5 escenas
    escenas = guion["escenas"][:5]
    num_escenas = len(escenas)

    audio_temp = AudioFileClip(audio_path)
    duracion_total = audio_temp.duration
    duracion_por_escena = duracion_total / num_escenas
    audio_temp.close()

    print(f"  ⏱️  Audio: {duracion_total:.1f}s — {num_escenas} escenas — {duracion_por_escena:.1f}s por escena")

    # Descargar imágenes EN PARALELO
    print("\n📸 Descargando imágenes en paralelo...")
    rutas_imagenes = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futuros = {
            executor.submit(
                descargar_imagen,
                escena["prompt_imagen"],
                escena["numero"],
                tema
            ): escena["numero"]
            for escena in escenas
        }
        for futuro in as_completed(futuros):
            num = futuros[futuro]
            try:
                ruta = futuro.result()
                rutas_imagenes[num] = ruta
            except Exception as e:
                print(f"  ❌ Error imagen {num}: {e}")
                rutas_imagenes[num] = crear_imagen_fallback("Error", num, tema)

    # Agregar subtítulos y crear clips
    print("\n🎨 Agregando subtítulos...")
    clips = []
    for escena in escenas:
        num = escena["numero"]
        texto = escena["texto_narrado"]
        ruta_img = rutas_imagenes.get(num)

        nombre_sub = nombre + f"_sub_{num}.png"
        ruta_sub = os.path.join(IMAGES_DIR, nombre_sub)
        agregar_subtitulo(ruta_img, texto, ruta_sub)

        clip = ImageClip(ruta_sub).with_duration(duracion_por_escena)
        clips.append(clip)

    print("\n🎞️  Ensamblando video...")
    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_path)
    video = video.with_audio(audio)

    ruta_video = os.path.join(OUTPUT_DIR, f"{nombre}.mp4")
    print(f"\n⏳ Exportando video...")

    video.write_videofile(
        ruta_video,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=1,
        logger=None,
        bitrate="500k"
    )

    guion["video"] = ruta_video
    guion["estado"] = "sin_cloudinary"
    guardar_guion(guion)

    print(f"\n✅ Video guardado: {ruta_video}")
    return ruta_video