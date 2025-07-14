from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn
import openai
import os
import tempfile

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process-audio")
async def process_audio(request: Request, file: UploadFile = File(...), lang: str = Form("es")):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript_response = openai.Audio.transcribe("whisper-1", audio_file)
            transcript = transcript_response["text"]

        if lang == "es":
            prompt = f"Corrige el siguiente texto y proporciona retroalimentación gramatical y una versión corregida:\nTexto: \"{transcript}\"."
        else:
            prompt = f"Correct the following Spanish text and give grammar feedback and a corrected version:\nText: \"{transcript}\"."

        chat_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un profesor de español que corrige y da retroalimentación de forma clara."},
                {"role": "user", "content": prompt}
            ]
        )

        feedback = chat_response.choices[0].message.content.strip()
        os.remove(tmp_path)

        return {
            "transcription": transcript,
            "feedback": feedback
        }

    except Exception as e:
        return {
            "transcription": "No se pudo transcribir el audio.",
            "feedback": "No se generó feedback.",
            "error": str(e)
        }