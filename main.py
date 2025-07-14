from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import openai
import tempfile
import os
import traceback

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...), lang: str = Form(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                language="es"
            )

        prompt = f'''Eres un profesor de español. El estudiante dijo: "{transcript}".
Corrige los errores gramaticales y sugiere una versión corregida.
Responde en {"español" if lang == "es" else "inglés"} con observaciones y una versión corregida.'''

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        feedback_text = response.choices[0].message.content.strip()

        parts = feedback_text.split("Suggested corrected version:")
        feedback = parts[0].strip()
        correction = parts[1].strip() if len(parts) > 1 else ""

        return {
            "transcription": transcript,
            "feedback": feedback,
            "correction": correction
        }

    except Exception as e:
        print("❌ Error procesando el audio:", str(e))
        traceback.print_exc()
        return {
            "transcription": "No se pudo transcribir el audio.",
            "feedback": "No se generó feedback.",
            "error": str(e)
        }
