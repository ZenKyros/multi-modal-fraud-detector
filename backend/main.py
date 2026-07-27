"""
Multi-Modal Fraud Detector: FastAPI Backend

Core orchestration layer that:
1. Manages WebSocket connections for real-time streaming
2. Coordinates parallel pillar processing (linguistic, behavioral, acoustic)
3. Runs the game-theoretic fusion engine
4. Gates through LLM verification when threat index > 0.55
5. Streams results back to frontend
"""

import os
import asyncio
import json
import numpy as np
from typing import Dict, Optional, List, Set
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Import agents and engine components
from agents.ingestion import AudioIngestionAgent
from agents.linguistic import LinguisticAgent
from agents.behavioral import BehavioralAgent
from agents.acoustic import AcousticAgent
from engine.game_theory import StackelbergGameEngine
from engine.llm_verifier import LLMVerifierGate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


# ============================================================================
# Pydantic Models for API Contracts
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request model for audio analysis."""
    audio_file: str
    chunk_index: int


class StrategyResponse(BaseModel):
    """Response model for game theory strategy."""
    defender_strategy: List[float]
    attacker_strategy: List[float]
    threat_history: List[float]
    payoff_matrix: List[List[float]]


class AnalysisResult(BaseModel):
    """Complete analysis result for a chunk."""
    chunk_index: int
    threat_index: float
    weights: List[float]
    pillar_scores: List[float]
    requires_verification: bool
    verification: Optional[Dict] = None
    transcript: str
    timestamp: str


# ============================================================================
# Global State Management
# ============================================================================

class AnalysisEngine:
    """Centralized analysis engine combining all pillars."""
    
    def __init__(self):
        """Initialize all analysis components."""
        self.ingestion = AudioIngestionAgent()
        self.linguistic = LinguisticAgent()
        self.behavioral = BehavioralAgent()
        self.acoustic = AcousticAgent()
        self.game_engine = StackelbergGameEngine()
        self.llm_verifier = LLMVerifierGate()
        
        # Track active sessions
        self.active_streams: Set[str] = set()
        self.analysis_results: Dict[str, List[AnalysisResult]] = {}

    async def process_live_audio(self, audio_data: bytes, session_id: str, chunk_index: int = 0) -> Dict:
        """
        Process live audio data from WebSocket stream.
        
        Args:
            audio_data: Raw audio bytes
            session_id: Unique session identifier
            chunk_index: Index for tracking (default 0 for live)
            
        Returns:
            Complete analysis result
        """
        try:
            import io
            import librosa
            
            logger.info(f"[{session_id}] Processing live audio ({len(audio_data)} bytes)")
            
            # Convert bytes to audio array
            audio_array, sr = librosa.load(io.BytesIO(audio_data), sr=None, mono=True)
            
            # If audio is longer than 3 seconds, take first 3 seconds
            max_samples = int(3.0 * sr)
            if len(audio_array) > max_samples:
                audio_array = audio_array[:max_samples]
            
            # Pad if shorter than 3 seconds
            if len(audio_array) < max_samples:
                audio_array = np.pad(audio_array, (0, max_samples - len(audio_array)))
            
            # Step 2: Parallel pillar processing
            linguistic_task = self.linguistic.process_chunk(audio_array, sr, chunk_index)
            behavioral_task = self.behavioral.process_chunk(audio_array, sr, chunk_index)
            acoustic_task = self.acoustic.process_chunk(audio_array, sr, chunk_index)
            
            # Wait for all pillars to complete
            linguistic_result = await linguistic_task
            behavioral_result = await behavioral_task
            acoustic_result = await acoustic_task
            
            # Step 3: Extract scores from each pillar
            linguistic_score = linguistic_result.get("urgency_score", 0.0)
            behavioral_score = behavioral_result.get("aggression_score", 0.0)
            acoustic_score = acoustic_result.get("environment_index", 0.0)
            
            # Step 4: Game-theoretic fusion
            fusion_result = self.game_engine.fuse_pillar_outputs(
                linguistic_score, behavioral_score, acoustic_score
            )
            
            threat_index = fusion_result["threat_index"]
            requires_verification = fusion_result["requires_verification"]
            
            # Step 5: Conditional LLM verification
            verification_result = None
            if requires_verification:
                logger.info(f"[{session_id}] Threat index {threat_index:.2f} exceeds threshold, running LLM verification...")
                verification_result = await self.llm_verifier.verify_fraud_alert(
                    linguistic_result.get("transcript", ""),
                    linguistic_result,
                    behavioral_result,
                    acoustic_result,
                    threat_index
                )
                
                # Adapt game strategy based on verification
                is_fraud = verification_result.get("is_fraud", False)
                is_verified = self.llm_verifier.is_response_valid(verification_result)
                
                self.game_engine.adapt_to_outcome(
                    (linguistic_score, behavioral_score, acoustic_score),
                    threat_index,
                    is_fraud,
                    is_verified
                )
            
            # Step 6: Package results
            result = {
                "chunk_index": chunk_index,
                "threat_index": threat_index,
                "weights": fusion_result["weights"],
                "pillar_scores": fusion_result["pillar_scores"],
                "contributions": fusion_result["contributions"],
                "requires_verification": requires_verification,
                "verification": verification_result,
                "transcript": linguistic_result.get("transcript", ""),
                "linguistic_data": {
                    "urgency_score": linguistic_score,
                    "keywords": linguistic_result.get("keywords", []),
                },
                "behavioral_data": {
                    "aggression_score": behavioral_score,
                    "dominance_score": behavioral_result.get("voice_features", {}).get("dominance_score", 0),
                },
                "acoustic_data": {
                    "environment_index": acoustic_score,
                    "noise_elevation": acoustic_result.get("noise_floor_features", {}).get("noise_elevation", 0),
                },
                "game_state": self.game_engine.get_strategy_metrics(),
                "timestamp": datetime.now().isoformat(),
                "is_live": True,
            }
            
            # Store result
            if session_id not in self.analysis_results:
                self.analysis_results[session_id] = []
            self.analysis_results[session_id].append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"[{session_id}] Error processing live audio: {str(e)}")
            raise

    async def process_chunk(
        self,
        audio_file: str,
        chunk_index: int,
        session_id: str
    ) -> Dict:
        """
        Process a single audio chunk through all pillars and fusion engine.
        
        Args:
            audio_file: Name of audio file to analyze
            chunk_index: Index of 3-second chunk to process
            session_id: Unique session identifier
            
        Returns:
            Complete analysis result
        """
        try:
            # Step 1: Load audio chunk
            chunk, sr, metadata = self.ingestion.get_chunk(audio_file, chunk_index)
            
            logger.info(f"[{session_id}] Processing chunk {chunk_index} from {audio_file}")
            
            # Step 2: Parallel pillar processing
            linguistic_task = self.linguistic.process_chunk(chunk, sr, chunk_index)
            behavioral_task = self.behavioral.process_chunk(chunk, sr, chunk_index)
            acoustic_task = self.acoustic.process_chunk(chunk, sr, chunk_index)
            
            # Wait for all pillars to complete
            linguistic_result = await linguistic_task
            behavioral_result = await behavioral_task
            acoustic_result = await acoustic_task
            
            # Step 3: Extract scores from each pillar
            linguistic_score = linguistic_result.get("urgency_score", 0.0)
            behavioral_score = behavioral_result.get("aggression_score", 0.0)
            acoustic_score = acoustic_result.get("environment_index", 0.0)
            
            # Step 4: Game-theoretic fusion
            fusion_result = self.game_engine.fuse_pillar_outputs(
                linguistic_score, behavioral_score, acoustic_score
            )
            
            threat_index = fusion_result["threat_index"]
            requires_verification = fusion_result["requires_verification"]
            
            # Step 5: Conditional LLM verification
            verification_result = None
            if requires_verification:
                logger.info(f"[{session_id}] Threat index {threat_index:.2f} exceeds threshold, running LLM verification...")
                verification_result = await self.llm_verifier.verify_fraud_alert(
                    linguistic_result.get("transcript", ""),
                    linguistic_result,
                    behavioral_result,
                    acoustic_result,
                    threat_index
                )
                
                # Adapt game strategy based on verification
                is_fraud = verification_result.get("is_fraud", False)
                is_verified = self.llm_verifier.is_response_valid(verification_result)
                
                self.game_engine.adapt_to_outcome(
                    (linguistic_score, behavioral_score, acoustic_score),
                    threat_index,
                    is_fraud,
                    is_verified
                )
            
            # Step 6: Package results
            result = {
                "chunk_index": chunk_index,
                "threat_index": threat_index,
                "weights": fusion_result["weights"],
                "pillar_scores": fusion_result["pillar_scores"],
                "contributions": fusion_result["contributions"],
                "requires_verification": requires_verification,
                "verification": verification_result,
                "transcript": linguistic_result.get("transcript", ""),
                "linguistic_data": {
                    "urgency_score": linguistic_score,
                    "keywords": linguistic_result.get("keywords", []),
                },
                "behavioral_data": {
                    "aggression_score": behavioral_score,
                    "dominance_score": behavioral_result.get("voice_features", {}).get("dominance_score", 0),
                },
                "acoustic_data": {
                    "environment_index": acoustic_score,
                    "noise_elevation": acoustic_result.get("noise_floor_features", {}).get("noise_elevation", 0),
                },
                "game_state": self.game_engine.get_strategy_metrics(),
                "timestamp": datetime.now().isoformat(),
            }
            
            # Store result
            if session_id not in self.analysis_results:
                self.analysis_results[session_id] = []
            self.analysis_results[session_id].append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"[{session_id}] Error processing chunk: {str(e)}")
            raise

    def get_available_files(self) -> List[str]:
        """Get list of available audio files."""
        return self.ingestion.get_available_files()

    def get_file_metadata(self, audio_file: str) -> Dict:
        """Get metadata about an audio file."""
        try:
            duration = self.ingestion.get_audio_duration(audio_file)
            return {
                "filename": audio_file,
                "duration": duration,
                "chunk_count": int(np.ceil(duration / 3.0)),
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# FastAPI Application Setup
# ============================================================================

# Global analysis engine instance
analysis_engine: Optional[AnalysisEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    global analysis_engine
    
    # Startup
    logger.info("Initializing Multi-Modal Fraud Detector...")
    analysis_engine = AnalysisEngine()
    logger.info("✓ Analysis engine initialized")
    logger.info(f"✓ Available audio files: {analysis_engine.get_available_files()}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if analysis_engine:
        analysis_engine.linguistic.clear_cache()
        analysis_engine.ingestion.clear_cache()


# Create FastAPI application
app = FastAPI(
    title="Multi-Modal Fraud Detector API",
    description="Real-time fraud detection using parallel LLM analysis and game theory",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected (total: {len(self.active_connections)})")
    
    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected (total: {len(self.active_connections)})")
    
    async def send_to_client(self, client_id: str, data: Dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {str(e)}")


manager = ConnectionManager()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/files")
async def get_available_files():
    """Get list of available audio files for analysis."""
    if not analysis_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    files = analysis_engine.get_available_files()
    return {
        "files": files,
        "count": len(files),
    }


@app.get("/api/files/{filename}/metadata")
async def get_file_metadata(filename: str):
    """Get metadata about a specific audio file."""
    if not analysis_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return analysis_engine.get_file_metadata(filename)


@app.post("/api/analyze")
async def analyze_chunk(request: AnalysisRequest):
    """Analyze a single audio chunk."""
    if not analysis_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    session_id = "api_session"
    result = await analysis_engine.process_chunk(request.audio_file, request.chunk_index, session_id)
    
    return result


@app.get("/api/strategy")
async def get_current_strategy():
    """Get current game-theoretic strategy."""
    if not analysis_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    metrics = analysis_engine.game_engine.get_strategy_metrics()
    return metrics


@app.get("/api/results/{session_id}")
async def get_session_results(session_id: str):
    """Get all analysis results for a session."""
    if not analysis_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    results = analysis_engine.analysis_results.get(session_id, [])
    return {
        "session_id": session_id,
        "chunk_count": len(results),
        "results": results,
    }


# ============================================================================
# WebSocket Endpoint for Real-Time Streaming
# ============================================================================

@app.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis streaming.
    
    Client sends: {"action": "analyze", "audio_file": "...", "chunk_index": ...}
    Server sends: Analysis results as they complete
    """
    if not analysis_engine:
        await websocket.close(code=1008, reason="Engine not initialized")
        return
    
    import uuid
    session_id = str(uuid.uuid4())[:8]
    
    try:
        await manager.connect(websocket, session_id)
        analysis_engine.active_streams.add(session_id)
        
        while True:
            # Wait for client message
            try:
                data = await websocket.receive_json()
            except Exception as e:
                logger.warning(f"[{session_id}] WebSocket receive error: {str(e)}")
                break
            
            action = data.get("action")
            
            if action == "analyze":
                # Process audio chunk
                try:
                    result = await analysis_engine.process_chunk(
                        data.get("audio_file", ""),
                        data.get("chunk_index", 0),
                        session_id
                    )
                    
                    # Send result back to client
                    await manager.send_to_client(session_id, {
                        "type": "analysis_result",
                        "data": result,
                    })
                    
                except Exception as e:
                    await manager.send_to_client(session_id, {
                        "type": "error",
                        "message": str(e),
                    })
            
            elif action == "analyze_live":
                # Process live audio from microphone
                try:
                    import base64
                    
                    # Decode base64 audio data
                    audio_data = base64.b64decode(data.get("audio_data", ""))
                    
                    # Process the live audio
                    result = await analysis_engine.process_live_audio(
                        audio_data,
                        session_id,
                        data.get("chunk_index", 0)
                    )
                    
                    # Send result back to client
                    await manager.send_to_client(session_id, {
                        "type": "analysis_result",
                        "data": result,
                    })
                    
                except Exception as e:
                    logger.error(f"[{session_id}] Live audio processing error: {str(e)}")
                    await manager.send_to_client(session_id, {
                        "type": "error",
                        "message": str(e),
                    })
            
            elif action == "get_strategy":
                # Send current strategy
                metrics = analysis_engine.game_engine.get_strategy_metrics()
                await manager.send_to_client(session_id, {
                    "type": "strategy_update",
                    "data": metrics,
                })
            
            elif action == "ping":
                # Health check
                await manager.send_to_client(session_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                })
    
    except Exception as e:
        logger.error(f"[{session_id}] WebSocket error: {str(e)}")
    
    finally:
        analysis_engine.active_streams.discard(session_id)
        await manager.disconnect(session_id)


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
