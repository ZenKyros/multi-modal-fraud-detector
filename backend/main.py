import os
import pathlib
import logging
import asyncio
import json
import tempfile
import subprocess
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import numpy as np
import wave

# ========== FORCE LOAD .env ==========
env_path = pathlib.Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print("✅ Loaded .env from:", env_path)
else:
    print("❌ .env file not found in", pathlib.Path(__file__).parent)

print(f"GROQ_API_KEY: {'✅ Set' if os.getenv('GROQ_API_KEY') else '❌ Missing'}")
print(f"GEMINI_API_KEY: {'✅ Set' if os.getenv('GEMINI_API_KEY') else '❌ Missing'}")
# =====================================

# Import agents and engines
from agents.ingestion import AudioIngestionAgent
from agents.linguistic import LinguisticPillar
from agents.behavioral import BehavioralPillar
from agents.acoustic import AcousticPillar
from engine.llm_verifier import LLMVerifier
from engine.bayesian_fusion import BayesianFusionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== Initialize Components ==========
app = FastAPI(title="Multi-Modal Fraud Detector", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ingestion_agent = AudioIngestionAgent(chunk_duration=10, sample_rate=16000)  # 10s chunks to reduce API calls
linguistic_pillar = LinguisticPillar()
behavioral_pillar = BehavioralPillar()
acoustic_pillar = AcousticPillar()
game_engine = BayesianFusionEngine()
llm_verifier = LLMVerifier()

active_connections: List[WebSocket] = []
transcript_history: List[Dict[str, Any]] = []

# ========== Helper Functions ==========

def save_chunk_to_wav(chunk: np.ndarray, file_path: str):
    """Save numpy audio chunk as WAV file."""
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(16000)
        chunk_int16 = (chunk * 32767).astype(np.int16)
        wf.writeframes(chunk_int16.tobytes())

async def process_audio_chunk(file_path: str) -> Dict[str, Any]:
    """Process a single audio chunk through all pillars."""
    try:
        linguistic_task = asyncio.create_task(linguistic_pillar.analyze(file_path))
        behavioral_task = asyncio.create_task(behavioral_pillar.analyze(file_path))
        acoustic_task = asyncio.create_task(acoustic_pillar.analyze(file_path))

        linguistic_result, behavioral_result, acoustic_result = await asyncio.gather(
            linguistic_task, behavioral_task, acoustic_task
        )

        pillar_results = {
            "linguistic": linguistic_result,
            "behavioral": behavioral_result,
            "acoustic": acoustic_result
        }

        threat_index = game_engine.calculate_threat_index(pillar_results)
        
        result = {
            "timestamp": asyncio.get_event_loop().time(),
            "pillar_results": pillar_results,
            "threat_index": threat_index,
            "strategy_weights": game_engine.get_strategy_weights()
        }

        if threat_index > 0.55:
            verification = await llm_verifier.verify(
                pillar_results,
                threat_index,
                transcript=linguistic_result.get("transcript", "")
            )
            result["verification"] = verification
            result["is_fraud"] = verification.get("is_fraud", False)
        else:
            result["is_fraud"] = False

        return result
    except Exception as e:
        logger.error(f"Error processing chunk: {str(e)}")
        return {"error": str(e)}

async def process_full_audio(file_path: str) -> Dict[str, Any]:
    """Process an entire audio file through ingestion and all chunks."""
    try:
        # Load audio
        audio = ingestion_agent.load_audio(file_path)
        if audio is None:
            return {"error": "Failed to load audio"}

        # Split into chunks
        chunks = ingestion_agent.chunk_audio(audio)
        logger.info(f"Split into {len(chunks)} chunks")

        # Process each chunk
        chunk_results = []
        all_transcripts = []  # collection of all transcripts

        for idx, chunk in enumerate(chunks):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            save_chunk_to_wav(chunk, tmp_path)
            
            try:
                result = await process_audio_chunk(tmp_path)
                chunk_results.append(result)
                trans = result.get("pillar_results", {}).get("linguistic", {}).get("transcript", "")
                if trans:
                    all_transcripts.append(trans)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        if not chunk_results:
            return {"error": "No chunks processed"}

        # Aggregate results
        avg_threat = sum(r.get("threat_index", 0) for r in chunk_results) / len(chunk_results)
        
        # Use last transcript (for backward compatibility)
        last_transcript = chunk_results[-1].get("pillar_results", {}).get("linguistic", {}).get("transcript", "")

        # Average pillar scores
        pillar_scores = {"linguistic": [], "behavioral": [], "acoustic": []}
        for r in chunk_results:
            for p in pillar_scores:
                pillar_scores[p].append(r.get("pillar_results", {}).get(p, {}).get("pillar_score", 0))

        avg_pillar = {p: sum(vals)/len(vals) if vals else 0 for p, vals in pillar_scores.items()}

        response = {
            "threat_index": avg_threat,
            "is_fraud": avg_threat > 0.55,
            "pillar_results": {
                "linguistic": {
                    "pillar_score": avg_pillar["linguistic"],
                    "transcript": last_transcript
                },
                "behavioral": {"pillar_score": avg_pillar["behavioral"]},
                "acoustic": {"pillar_score": avg_pillar["acoustic"]}
            },
            "transcripts": all_transcripts,  # full list
            "strategy_weights": game_engine.get_strategy_weights(),
            "chunks_processed": len(chunk_results)
        }

        # Trigger LLM verification if fraud detected
        if avg_threat > 0.55:
            verification = await llm_verifier.verify(
                response["pillar_results"],
                avg_threat,
                transcript=last_transcript
            )
            response["verification"] = verification
            response["is_fraud"] = verification.get("is_fraud", False)

        return response

    except Exception as e:
        logger.error(f"Full audio processing error: {str(e)}")
        return {"error": str(e)}

# ========== API Endpoints ==========

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY"))
        }
    }

@app.post("/api/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Upload and analyze an audio file."""
    try:
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        result = await process_full_audio(temp_path)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze_text")
async def analyze_text(request: Request):
    """Analyze a pasted conversation text for fraud indicators."""
    try:
        data = await request.json()
        text = data.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Use linguistic pillar to analyze
        urgency = linguistic_pillar.calculate_urgency_score(text)
        keywords = linguistic_pillar.detect_keywords(text)
        pillar_score = min(1.0, urgency + len(keywords) * 0.05)
        
        # Mock other pillars (since we don't have audio)
        threat_index = pillar_score
        
        result = {
            "threat_index": threat_index,
            "is_fraud": threat_index > 0.55,
            "pillar_results": {
                "linguistic": {
                    "pillar_score": pillar_score,
                    "transcript": text[:500],
                    "urgency_score": urgency,
                    "keyword_matches": keywords,
                    "keyword_count": len(keywords)
                },
                "behavioral": {"pillar_score": 0.3},
                "acoustic": {"pillar_score": 0.2}
            },
            "strategy_weights": game_engine.get_strategy_weights(),
            "transcripts": [text[:500]]
        }
        
        if threat_index > 0.55:
            verification = await llm_verifier.verify(
                result["pillar_results"],
                threat_index,
                transcript=text[:1000]
            )
            result["verification"] = verification
            result["is_fraud"] = verification.get("is_fraud", False)
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Text analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategy")
async def get_strategy():
    return game_engine.get_strategy_weights()

@app.get("/api/transcripts")
async def get_transcripts(limit: int = 50):
    return {"transcripts": transcript_history[-limit:]}

@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info("WebSocket connected")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                audio_data = json.loads(data)

                if audio_data.get("type") == "audio_chunk":
                    chunk_data = audio_data.get("data")
                    import base64
                    audio_bytes = base64.b64decode(chunk_data)

                    # Convert webm bytes to audio using ffmpeg
                    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
                        f.write(audio_bytes)
                        webm_path = f.name

                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f2:
                        wav_path = f2.name

                    try:
                        cmd = [
                            'ffmpeg', '-i', webm_path,
                            '-acodec', 'pcm_s16le',
                            '-ar', '16000',
                            '-ac', '1',
                            wav_path,
                            '-y'
                        ]
                        subprocess.run(cmd, capture_output=True, check=True, timeout=15)

                        # Process the chunk
                        result = await process_audio_chunk(wav_path)

                        # Send result
                        await websocket.send_text(json.dumps({
                            "type": "analysis_result",
                            "data": result
                        }))

                        if "transcript" in result.get("pillar_results", {}).get("linguistic", {}):
                            transcript_history.append({
                                "timestamp": result.get("timestamp"),
                                "text": result["pillar_results"]["linguistic"]["transcript"],
                                "threat_index": result.get("threat_index", 0)
                            })

                    except Exception as e:
                        logger.error(f"Chunk processing error: {str(e)}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": str(e)
                        }))
                    finally:
                        for f in [webm_path, wav_path]:
                            if os.path.exists(f):
                                os.remove(f)

                elif audio_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)