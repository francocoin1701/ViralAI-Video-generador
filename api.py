# api.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from src.generator.script_generator import generar_guion, guardar_guion
from src.generator.voice_generator import generar_audio
from src.editor.video_editor import generar_video
from src.generator.script_generator import listar_guiones

app = FastAPI(title="ViralAI API", version="1.0.0")

# CORS para que MeDo pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MODELOS ===
class VideoRequest(BaseModel):
    tema: str
    proveedor: str = "gemini"
    api_key: str
    duracion: int = 30
    estilo: str = "educativo"

class StatusResponse(BaseModel):
    status: str
    mensaje: str
    data: Optional[dict] = None

# === ENDPOINTS ===

@app.get("/")
def root():
    return {"mensaje": "ViralAI API funcionando 🚀", "version": "1.0.0"}

@app.get("/proveedores")
def get_proveedores():
    """Lista los proveedores de IA disponibles"""
    from config.settings import PROVIDERS_TEXTO
    return {
        "proveedores": [
            {"id": k, "nombre": v["nombre"], "modelo": v["modelo"]}
            for k, v in PROVIDERS_TEXTO.items()
        ]
    }

@app.post("/generar-guion")
def endpoint_generar_guion(request: VideoRequest):
    """Genera el guión del video"""
    try:
        guion = generar_guion(
            tema=request.tema,
            duracion=request.duracion,
            estilo=request.estilo,
            proveedor=request.proveedor,
            api_key=request.api_key
        )
        return {"status": "ok", "guion": guion}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generar-voz")
def endpoint_generar_voz(request: VideoRequest):
    """Genera la voz del guión"""
    try:
        from src.generator.script_generator import ya_existe, _nombre_archivo
        import json

        if not ya_existe(request.tema):
            raise HTTPException(status_code=404, detail="Primero genera el guión")

        with open(_nombre_archivo(request.tema), 'r', encoding='utf-8') as f:
            guion = json.load(f)

        ruta_audio = generar_audio(guion)
        return {"status": "ok", "audio": ruta_audio}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generar-video")
def endpoint_generar_video(request: VideoRequest):
    """Genera el video completo"""
    try:
        from src.generator.script_generator import ya_existe, _nombre_archivo
        import json

        if not ya_existe(request.tema):
            raise HTTPException(status_code=404, detail="Primero genera el guión")

        with open(_nombre_archivo(request.tema), 'r', encoding='utf-8') as f:
            guion = json.load(f)

        if guion.get("estado") == "sin_voz":
            raise HTTPException(status_code=400, detail="Primero genera la voz")

        ruta_video = generar_video(guion)
        return {"status": "ok", "video": ruta_video}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generar-todo")
def endpoint_generar_todo(request: VideoRequest):
    """Genera guión + voz + video en un solo llamado"""
    try:
        # 1. Guión
        print(f"📝 Generando guión: {request.tema}")
        guion = generar_guion(
            tema=request.tema,
            duracion=request.duracion,
            estilo=request.estilo,
            proveedor=request.proveedor,
            api_key=request.api_key
        )

        # 2. Voz
        print(f"🎙️  Generando voz...")
        ruta_audio = generar_audio(guion)

        # 3. Video
        print(f"🎬 Generando video...")
        ruta_video = generar_video(guion)

        return {
            "status": "ok",
            "tema": request.tema,
            "titulo": guion["titulo"],
            "hashtags": guion["hashtags"],
            "descripcion_youtube": guion["descripcion_youtube"],
            "descripcion_tiktok": guion["descripcion_tiktok"],
            "video": ruta_video
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/videos")
def listar_videos():
    """Lista todos los videos generados"""
    guiones = listar_guiones(estado="completo")
    return {
        "total": len(guiones),
        "videos": [
            {
                "tema": g["tema"],
                "titulo": g["titulo"],
                "video": g.get("video", ""),
                "hashtags": g["hashtags"]
            }
            for g in guiones
        ]
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)