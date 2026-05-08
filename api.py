# api.py
import os
import uuid
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

from src.generator.script_generator import generar_guion, listar_guiones
from src.generator.voice_generator import generar_audio
from src.editor.video_editor import generar_video

app = FastAPI(title="ViralAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Estado en memoria de los jobs
jobs = {}

class VideoRequest(BaseModel):
    tema: str
    proveedor: str = "gemini"
    api_key: str
    duracion: int = 30
    estilo: str = "educativo"

def procesar_video(job_id: str, tema: str, proveedor: str, api_key: str, duracion: int, estilo: str):
    try:
        jobs[job_id]["status"] = "generating_script"
        jobs[job_id]["mensaje"] = "Generando guión..."
        guion = generar_guion(tema=tema, duracion=duracion, estilo=estilo, proveedor=proveedor, api_key=api_key)

        jobs[job_id]["status"] = "generating_voice"
        jobs[job_id]["mensaje"] = "Generando voz..."
        ruta_audio = generar_audio(guion)

        jobs[job_id]["status"] = "generating_video"
        jobs[job_id]["mensaje"] = "Generando video..."
        ruta_video = generar_video(guion)

        jobs[job_id]["status"] = "uploading"
        jobs[job_id]["mensaje"] = "Subiendo a la nube..."
        resultado = cloudinary.uploader.upload(
            ruta_video,
            resource_type="video",
            folder="viralai",
            public_id=os.path.basename(ruta_video).replace(".mp4", ""),
            overwrite=True
        )
        video_url = resultado["secure_url"]

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["mensaje"] = "Video listo!"
        jobs[job_id]["resultado"] = {
            "status": "ok",
            "tema": tema,
            "titulo": guion["titulo"],
            "hashtags": guion["hashtags"],
            "descripcion_youtube": guion["descripcion_youtube"],
            "descripcion_tiktok": guion["descripcion_tiktok"],
            "video_url": video_url
        }

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["mensaje"] = str(e)

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

@app.post("/generar-todo")
def endpoint_generar_todo(request: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "starting",
        "mensaje": "Iniciando...",
        "resultado": None
    }
    background_tasks.add_task(
        procesar_video,
        job_id,
        request.tema,
        request.proveedor.lower(),
        request.api_key,
        request.duracion,
        request.estilo
    )
    return {"job_id": job_id, "status": "started"}

@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return jobs[job_id]

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
                "video_url": g.get("video_url", ""),
                "hashtags": g["hashtags"]
            }
            for g in guiones
        ]
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)