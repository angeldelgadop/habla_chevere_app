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
            prompt = f"""
Analiza el siguiente texto en español. Si hay errores gramaticales, de vocabulario o de estructura, indícalos claramente. 
Si el texto está bien, solo dilo y no inventes errores. Usa el siguiente formato:

1. 🧠 Observaciones generales:
   - ...

2. 📌 Errores específicos:
   - ❌ Error: ...
     💡 Explicación: ...
     ✅ Corrección: ...

3. ✍️ Versión corregida sugerida (si hubo errores):
   ...

Texto del estudiante:
"""{transcript}"""
"""
            system_msg = "Eres un profesor de español que da retroalimentación clara y amable en español latinoamericano."
        else:
            prompt = f"""
Analyze the following Spanish text. If there are grammar, vocabulary or structural errors, point them out clearly. 
If the text is fine, just say so and do not invent problems. Use the following format:

1. 🧠 General observations:
   - ...

2. 📌 Specific mistakes:
   - ❌ Error: ...
     💡 Explanation: ...
     ✅ Correction: ...

3. ✍️ Suggested corrected version (if needed):
   ...

Student's text:
"""{transcript}"""
"""
            system_msg = "You are a Spanish teacher who provides friendly and clear feedback in English."

        chat_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_msg},
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
