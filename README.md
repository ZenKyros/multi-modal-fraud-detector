# Multi-Modal Fraud Detector

A real-time, game-theoretic audio analysis system that detects fraud calls through parallel AI pillar processing and adaptive machine learning.

## Overview

This application uses an asymmetric **Stackelberg Security Game** to intercept scam calls by analyzing incoming audio in 3-second segments across three specialized analytical pillars:

- **Pillar I (Linguistic)**: Groq Whisper Large-v3 API for real-time transcription and urgency keyword detection
- **Pillar II (Behavioral)**: Local CPU-based Librosa analysis for speaker dominance, volume pressure, and speech-to-pause ratios
- **Pillar III (Acoustic)**: Local CPU-based background noise signature classification (fraud center vs. domestic ambient)

A **Game-Theoretic Fusion Engine** dynamically reweights these pillars in real-time. When the combined threat index exceeds 0.55, output gates through a **Gemini LLM Verifier** enforcing strict JSON schema validation before alerting the user.

## System Architecture

```
Backend (FastAPI @ localhost:8000)
├── Audio Ingestion Agent (3-second chunking)
├── Parallel Pillar Processors
│   ├── Linguistic (Groq API)
│   ├── Behavioral (Librosa)
│   └── Acoustic (Librosa)
├── Game Theory Fusion Engine
└── LLM Verifier Gate (Gemini API)

Frontend (React/Vite @ localhost:5173)
├── Real-time Dashboard
├── Telemetry Cards (Pillar I, II, III)
├── Nash Equilibrium Strategy Chart
├── Live Transcript Viewer
└── Threat Alert Banner
```

## Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **API Keys**:
  - Groq API key (free tier available at groq.com)
  - Google Gemini API key (free tier available at makersuite.google.com)

## Installation & Setup

### 1. Backend Setup

```bash
cd multi-modal-fraud-detector
cd backend

# Create virtual environment
python -m venv venv

# Activate venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt

# Configure API keys
# Edit .env and add your GROQ_API_KEY and GEMINI_API_KEY
```

### 2. Frontend Setup

```bash
cd multi-modal-fraud-detector/frontend

# Install dependencies
npm install

# Create .env.local with API endpoint
# Content: VITE_API_URL=http://localhost:8000
```

## Running the Application

### Terminal 1: Start Backend (FastAPI)

```bash
cd multi-modal-fraud-detector/backend

# Activate venv first (if not already active)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Start Frontend (React/Vite)

```bash
cd multi-modal-fraud-detector/frontend

npm run dev
```

Access the application at `http://localhost:5173`

## API Endpoints

### WebSocket
- **WS**: `ws://localhost:8000/ws/analyze` - Real-time stream analysis

### REST Endpoints
- **POST** `/api/analyze` - Analyze audio file
- **POST** `/api/strategy` - Get current game theory weights
- **GET** `/api/transcripts` - Fetch live transcript
- **GET** `/api/health` - Health check

## Audio Data

Place test audio files in `backend/data/`:
- `normal_call.wav` - Baseline normal call
- `scam_call.wav` - Fraud scenario

The ingestion agent will automatically chunk these based on client requests.

## Game Theory Model

The fusion engine maintains a **payoff matrix** that evolves as the fraudster adapts:

```
Strategy Space: [Linguistic, Behavioral, Acoustic]
Payoff Matrix: 3x3 (Defender vs. Attacker strategies)
Nash Equilibrium Solver: Computes mixed strategy from current game state
Reweighting: Dynamic lambda adjustments based on pillar effectiveness
Threat Index Threshold: 0.55 (gates LLM verification)
```

## Configuration

Edit these files to customize behavior:

- `.env.development` - Global environment variables
- `backend/.env` - Cloud API keys and debug settings
- `frontend/.env.local` - React API endpoint

## Architecture Principles

1. **Modular Agents**: Each pillar is an independent module with clear input/output
2. **Async/Await**: Non-blocking I/O for parallel processing
3. **Type Safety**: Pydantic models for all API contracts
4. **CPU-Efficient**: Librosa operations run on CPU without GPU requirement
5. **Lightweight Frontend**: React hooks + Tailwind CSS for responsive UI
6. **Game-Theoretic Adaptation**: Real-time reweighting based on threat evolution

## File Structure

```
multi-modal-fraud-detector/
├── .env.development
├── requirements.txt
├── package.json
├── README.md
├── backend/
│   ├── .env
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ingestion.py
│   │   ├── linguistic.py
│   │   ├── behavioral.py
│   │   └── acoustic.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── game_theory.py
│   │   └── llm_verifier.py
│   └── data/
│       ├── normal_call.wav
│       └── scam_call.wav
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── .env.local
    ├── public/
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── components/
        │   ├── Sidebar.jsx
        │   ├── TelemetryCard.jsx
        │   ├── StrategyChart.jsx
        │   ├── Transcript.jsx
        │   └── AlertBanner.jsx
        ├── hooks/
        │   └── useWebSocket.js
        └── assets/
            └── index.css
```

## Troubleshooting

**CORS Issues**: Ensure frontend URL is in `CORS_ORIGINS` in `backend/.env`

**API Key Errors**: Verify `GROQ_API_KEY` and `GEMINI_API_KEY` are set correctly

**Audio Issues**: Ensure `.wav` files are mono/stereo at 16kHz for optimal Librosa performance

**WebSocket Connection Failed**: Check backend is running on port 8000 and frontend API URL is correct

## Performance Metrics

- **Transcription Latency**: ~2-3 seconds (Groq API, dependent on audio quality)
- **Behavioral Analysis**: ~500ms per 3-second chunk (local Librosa)
- **Acoustic Analysis**: ~300ms per 3-second chunk (local Librosa)
- **Game Theory Reweighting**: ~50ms (matrix operations on CPU)
- **LLM Verification**: ~1-2 seconds (Gemini API, if threat index > 0.55)

## Future Enhancements

- Multi-language support via Groq Whisper variants
- Persistent threat history database
- Custom threat model training
- Mobile app deployment
- Advanced visualization of game state evolution

## License

MIT

## Support

For issues or questions, please refer to the inline documentation in each module.
