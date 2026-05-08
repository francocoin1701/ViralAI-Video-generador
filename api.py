# api.py
import os
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

from src.generator.script_generator import generar_guion, guardar_guion, listar_guiones
from src.generator.voice_generator import generar_audio
from src.editor.video_editor import generar_video

app = FastAPI(title="ViralAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
     allow_origins=[
        "https://app-bhp20zjdwflt.appmedo.com",
        "https://app-bhlzh2b2ru9t.appmedo.com",
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

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

@app.get("/")
def root():
    return {"mensaje": "ViralAI API funcionando 🚀", "version": "1.0.0"}

@app.get("/proveedores")
def get_proveedores():
    from config.settings import PROVIDERS_TEXTO
    return {
        "proveedores": [
            {"id": k, "nombre": v["nombre"], "modelo": v["modelo"]}
            for k, v in PROVIDERS_TEXTO.items()
        ]
    }

@app.post("/generar-guion")
def endpoint_generar_guion(request: VideoRequest):
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
    try:
        print(f"📝 Generando guión: {request.tema}")
        guion = generar_guion(
            tema=request.tema,
            duracion=request.duracion,
            estilo=request.estilo,
            proveedor=request.proveedor,
            api_key=request.api_key
        )

        print(f"🎙️  Generando voz...")
        ruta_audio = generar_audio(guion)

        print(f"🎬 Generando video...")
        ruta_video = generar_video(guion)

        print(f"☁️  Subiendo a Cloudinary...")
        resultado = cloudinary.uploader.upload(
            ruta_video,
            resource_type="video",
            folder="viralai",
            public_id=os.path.basename(ruta_video).replace(".mp4", ""),
            overwrite=True
        )
        video_url = resultado["secure_url"]
        print(f"✅ Video en Cloudinary: {video_url}")

        return {
            "status": "ok",
            "tema": request.tema,
            "titulo": guion["titulo"],
            "hashtags": guion["hashtags"],
            "descripcion_youtube": guion["descripcion_youtube"],
            "descripcion_tiktok": guion["descripcion_tiktok"],
            "video": ruta_video,
            "video_url": video_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/video/{nombre}")
def descargar_video(nombre: str):
    ruta = os.path.join("assets", "output", nombre)
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Video no encontrado")
    return FileResponse(ruta, media_type="video/mp4", filename=nombre)

@app.get("/videos")
def listar_videos():
    guiones = listar_guiones(estado="completo")
    return {
        "total": len(guiones),
        "videos": [
            {
                "tema": g["tema"],
                "titulo": g["titulo"],
                "video": g.get("video", ""),
                "video_url": g.get("video_url", ""),
                "hashtags": g["hashtags"]
            }
            for g in guiones
        ]
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)