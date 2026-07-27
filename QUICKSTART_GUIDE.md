# Quick Integration Guide

## Post-Build Checklist

### 1. **Set Up API Keys**

Get your free API keys:

#### Groq API Key
1. Visit https://console.groq.com/
2. Sign up for free account
3. Navigate to API keys
4. Copy your API key

#### Google Gemini API Key
1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy your API key

### 2. **Configure Environment**

Edit `backend/.env`:
```
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

### 3. **Install Dependencies**

```bash
# Backend
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r ../requirements.txt

# Frontend
cd ../frontend
npm install
```

### 4. **Start Services**

**Terminal 1 - Backend**:
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

### 5. **Access Dashboard**

Open browser: http://localhost:5173

---

## Troubleshooting

### Backend won't start
```bash
# Verify Python installation
python --version  # Should be 3.11+

# Check all dependencies installed
pip list | grep -E "(fastapi|librosa|groq|google)"

# Try installing individually
pip install fastapi uvicorn librosa groq google-generativeai
```

### Frontend build errors
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Try specific Tailwind version
npm install tailwindcss@3.3.6 -D
```

### WebSocket connection failed
- Ensure backend is running on port 8000
- Check VITE_API_URL in frontend/.env.local
- Check browser console for CORS errors
- Verify firewall isn't blocking port 8000

### API Key errors
- Copy API key exactly (no extra spaces)
- For Groq: Key should start with `gsk_`
- For Gemini: Key should start with `AIza`
- Restart backend after updating .env

### Audio file not found
- Ensure .wav files exist in `backend/data/`
- Check file names match exactly
- Files must be valid WAV format (16-bit, mono or stereo)

---

## Project File Summary

### Backend Structure
```
backend/
├── main.py                 # FastAPI orchestrator (447 lines)
├── .env                    # API key configuration
├── agents/
│   ├── ingestion.py       # Audio chunking (200 lines)
│   ├── linguistic.py      # Groq transcription (280 lines)
│   ├── behavioral.py      # Librosa speaker analysis (340 lines)
│   └── acoustic.py        # Librosa environment detection (320 lines)
├── engine/
│   ├── game_theory.py     # Stackelberg game solver (380 lines)
│   └── llm_verifier.py    # Gemini verification (290 lines)
└── data/
    ├── normal_call.wav    # Test audio (optional)
    └── scam_call.wav      # Test audio (optional)
```

### Frontend Structure
```
frontend/
├── src/
│   ├── main.jsx           # React entry (19 lines)
│   ├── App.jsx            # Root component (235 lines)
│   ├── components/
│   │   ├── Sidebar.jsx    # File/chunk controls (245 lines)
│   │   ├── TelemetryCard.jsx  # Pillar score display (70 lines)
│   │   ├── StrategyChart.jsx  # Game theory visualization (220 lines)
│   │   ├── Transcript.jsx     # Live transcript (50 lines)
│   │   └── AlertBanner.jsx    # Threat warnings (175 lines)
│   ├── hooks/
│   │   └── useWebSocket.js    # WebSocket manager (105 lines)
│   └── assets/
│       └── index.css      # Tailwind + custom styles (200 lines)
├── package.json           # Dependencies
├── vite.config.js         # Build configuration
├── tailwind.config.js     # Theme configuration
└── index.html            # HTML template
```

---

## Key Features Implemented

✅ **Real-time WebSocket streaming** - Bidirectional communication with backend
✅ **Three parallel analysis pillars** - Linguistic, Behavioral, Acoustic
✅ **Groq Whisper integration** - Cloud-based speech-to-text
✅ **Local Librosa analysis** - CPU-efficient audio feature extraction
✅ **Game theory engine** - Stackelberg security game with CFR
✅ **Gemini LLM verification** - Semantic fraud confirmation
✅ **Adaptive weighting** - Dynamic pillar reweighting based on outcomes
✅ **Responsive UI** - Dark cyber theme with Tailwind CSS
✅ **Real-time visualization** - Recharts for strategy & threat metrics
✅ **Live transcripts** - Scrolling text display of audio
✅ **Threat level indicators** - Color-coded safety zones
✅ **Auto-play mode** - Sequential chunk analysis
✅ **Session management** - Results persistence per session

---

## Performance Tuning

### For Production Deployment

```python
# backend/main.py
# Increase worker count for parallel streams
# uvicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Add rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

# Add request timeout
@app.post("/api/analyze")
@limiter.limit("100/minute")
async def analyze_chunk(...):
    ...
```

### For Frontend

```javascript
// frontend/vite.config.js
export default defineConfig({
  build: {
    minify: 'terser',
    rollupOptions: {
      output: {
        // Code splitting for lazy loading
        manualChunks: {
          'recharts': ['recharts'],
          'vendor': ['react', 'react-dom'],
        }
      }
    }
  }
})
```

---

## Deployment Options

### Option 1: Local Development
- Simplest setup
- Run `python -m uvicorn main:app --reload`
- Perfect for testing

### Option 2: Docker Deployment
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

### Option 3: Cloud Deployment (AWS Lambda, Google Cloud Functions)
- FastAPI compatible with serverless via Mangum adapter
- Frontend deployed to S3 + CloudFront
- Groq/Gemini APIs called directly from edge

---

## Development Workflow

### Adding a Feature

1. **Design**: Sketch component/function layout
2. **Implement Backend**: Add to appropriate agent/engine
3. **Test API**: Use curl or Postman
4. **Implement Frontend**: Create React component
5. **Test WebSocket**: Browser DevTools network tab
6. **Style**: Apply Tailwind classes
7. **Integrate**: Wire up state management

### Debugging Tips

```bash
# View backend logs
tail -f backend_logs.txt

# Check WebSocket messages
# Browser DevTools → Network → WS → Messages

# Profile performance
import time
start = time.time()
# ... code ...
print(f"Elapsed: {time.time() - start:.2f}s")
```

---

## API Rate Limits

| Service | Limit | Cost |
|---------|-------|------|
| Groq Whisper | 30 req/min (free) | Free tier |
| Google Gemini | 60 req/min (free) | Free tier |
| Local Librosa | Unlimited | CPU-bound |

---

## Next Steps After Setup

1. **Record test audio** or use provided samples
2. **Experiment with weights** in game_theory.py
3. **Customize keywords** in linguistic.py for your use case
4. **Integrate with external systems** (CRM, logging, alerting)
5. **Deploy to production** with proper monitoring

---

## Support & Resources

- **FastAPI Docs**: http://localhost:8000/docs (auto-generated)
- **Groq API**: https://groq.com/docs
- **Google Gemini**: https://ai.google.dev/docs
- **Librosa**: https://librosa.org/doc/latest/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Recharts**: https://recharts.org/guide

---

Created with ❤️ by AI Solutions Architect
