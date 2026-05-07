# src/generator/voice_generator.py
from gtts import gTTS
import os, json
from config.settings import AUDIO_DIR
from src.generator.script_generator import listar_guiones, guardar_guion

os.makedirs(AUDIO_DIR, exist_ok=True)

def generar_audio(guion: dict) -> str:
    nombre = guion["tema"].lower().replace(" ", "_")
    nombre = ''.join(c for c in nombre if c.isalnum() or c == '_')
    ruta_audio = os.path.join(AUDIO_DIR, f"{nombre}.mp3")
    
    tts = gTTS(text=guion["guion_completo"], lang="es", slow=False)
    tts.save(ruta_audio)
    
    guion["audio"] = ruta_audio
    guion["estado"] = "sin_video"
    guardar_guion(guion)
    
    print(f"🎙️  Audio generado: {ruta_audio}")
    return ruta_audio

if __name__ == "__main__":
    print("🎙️  GENERADOR DE VOCES")
    print("="*60)
    
    pendientes = listar_guiones(estado="sin_voz")
    
    if not pendientes:
        print("✅ No hay guiones pendientes de voz.")
        exit()
    
    print(f"\n📂 Guiones sin voz ({len(pendientes)}):")
    for i, g in enumerate(pendientes, 1):
        print(f"  {i}. {g['tema']} — {g['titulo']}")
    
    print(f"\n  0. Generar TODOS ({len(pendientes)})")
    
    opcion = input("\n¿Cuál generar? (número o 0 para todos): ").strip()
    
    if opcion == "0":
        seleccionados = pendientes
    elif opcion.isdigit() and 1 <= int(opcion) <= len(pendientes):
        seleccionados = [pendientes[int(opcion) - 1]]
    else:
        print("❌ Opción inválida")
        exit()
    
    for g in seleccionados:
        print(f"\n⏳ Generando voz para: {g['tema']}...")
        generar_audio(g)
    
    print("\n✅ Voces generadas!")