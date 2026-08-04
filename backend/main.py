# main.py
import os
import sys
import asyncio
import tempfile
import logging
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import subprocess


from agents.ingestion import IngestionAgent
from agents.linguistic import LinguisticAgent
from agents.acoustic import AcousticAgent
from agents.behavioral import BehavioralAgent
from engine.llm_verifier import LLMVerifier
from engine.bayesian_fusion import BayesianFusion

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fraud Call Detector")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Initialize agents
ingestion = IngestionAgent(model_size="base", device="cpu")
linguistic = LinguisticAgent()
acoustic = AcousticAgent()
behavioral = BehavioralAgent()

llm_verifier = LLMVerifier()
fusion = BayesianFusion()

# ────────── REST endpoints ──────────

@app.post("/analyze-text")
async def analyze_text(transcript: str = Form(...)):
    """
    Analyze pasted transcript text.
    """
    # Process text into segments
    processed = ingestion.process_text(transcript)
    return await run_analysis_pipeline(processed, audio_data=None)

@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    """
    Upload audio file for analysis.
    """
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Transcribe
        transcribed = ingestion.process_audio_file(tmp_path)
        if "error" in transcribed:
            return {"error": transcribed["error"]}

        # Load audio data for acoustic analysis
        import soundfile as sf
        audio_data, sr = sf.read(ingestion.convert_to_wav(tmp_path), dtype='float32')
        if sr != 16000:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)

        return await run_analysis_pipeline(transcribed, audio_data=audio_data)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# ────────── WebSocket for live audio demo ──────────

ws_headers: dict[WebSocket, bytes] = {}

@app.websocket("/ws/live-audio")
async def websocket_live_audio(websocket: WebSocket):
    await websocket.accept()
    buffer = bytearray()
    try:
        while True:
            data = await websocket.receive_bytes()
            # If this is the first chunk from this connection, save it as header
            if websocket not in ws_headers:
                ws_headers[websocket] = data
                logger.info("WebM header saved")
                continue   # wait for more data before processing

            buffer.extend(data)

            # Process every ~3 seconds of audio (accumulated chunks)
            if len(buffer) >= 30000:   # adjust based on average chunk size
                # Prepend header to make a valid WebM file
                full_data = ws_headers[websocket] + buffer

                ext = ".webm"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(full_data)
                    tmp_path = tmp.name

                # Convert to WAV
                wav_path = tmp_path + ".wav"
                cmd = [
                    "ffmpeg", "-i", tmp_path,
                    "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                    "-y", wav_path
                ]
                result_conv = subprocess.run(cmd, capture_output=True, text=True)
                if result_conv.returncode != 0:
                    logger.error(f"ffmpeg error: {result_conv.stderr}")
                    os.remove(tmp_path)
                    buffer = bytearray()
                    continue

                # Transcribe
                transcribed = ingestion.transcribe(wav_path)
                transcript_text = transcribed.get("text", "")

                if transcript_text:
                    result = await run_analysis_pipeline(transcribed, audio_data=None)
                    await websocket.send_json({
                        "type": "analysis",
                        "transcript": transcript_text,
                        "result": result
                    })

                # Cleanup
                os.remove(tmp_path)
                os.remove(wav_path)
                buffer = bytearray()   # reset chunk buffer (header stays)

    except WebSocketDisconnect:
        logger.info("Live audio disconnected")
        # Remove stored header when connection drops
        ws_headers.pop(websocket, None)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_headers.pop(websocket, None)

# ────────── Core Analysis Pipeline ──────────

async def run_analysis_pipeline(transcribed: dict, audio_data=None):
    transcript = transcribed.get("text", "")
    segments = transcribed.get("segments", [])



    # 2. Linguistic
    ling_result = linguistic.analyze(transcript)

    # 3. Acoustic (if audio available)
    ac_result = acoustic.analyze(audio_data) if audio_data is not None else acoustic._empty_result()

    # 4. Behavioral (if segments have speaker info)
    beh_result = behavioral.analyze(segments)

    # 5. LLM Verifier
    llm_result = await llm_verifier.analyze(transcript)

    # 6. Bayesian Fusion
    final = fusion.fuse( llm_result, ling_result, beh_result, ac_result)

    return {
        "transcript": transcript,
        "analysis": final,
        "details": {
            "linguistic": ling_result,
            "acoustic": ac_result,
            "behavioral": beh_result,
            "llm_raw": llm_result
        }
    }

# ────────── Entry point ──────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)