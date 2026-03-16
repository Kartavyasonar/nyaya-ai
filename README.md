# ⚖️ NYAYA AI — न्याय सबके लिए

> **India's first AI-powered legal rights assistant. Free. Multilingual. For 700 million Indians.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)

---

## 🇮🇳 What is NYAYA AI?

NYAYA AI answers any legal question in 22 Indian languages — instantly and for free. It knows every Act, every Section, every Supreme Court judgment that matters to ordinary Indians.

**Ask it anything:**
- "मेरा मालिक वेतन नहीं दे रहा — मैं क्या करूं?"
- "My landlord cut water and electricity to evict me. Is this legal?"
- "RTI कैसे दाखिल करें अपने ration card के लिए?"
- "What are my rights if police arrest me without warrant?"

It gives step-by-step answers with exact Act/Section citations, generates legal documents (RTI, FIR drafts, legal notices), and connects to free legal aid.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACES                       │
│   Web App    │   WhatsApp Bot   │   SMS   │   Voice     │
└──────────────┬──────────────────┬─────────┬─────────────┘
               │                  │         │
               ▼                  ▼         ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│  /query/ask  │  /documents/generate  │  /whatsapp/webhook│
└──────────────┬──────────────────────────────────────────┘
               │
       ┌───────┴───────────┐
       ▼                   ▼
┌─────────────┐    ┌──────────────────────────────────────┐
│  Groq LLM   │    │          RAG PIPELINE                │
│ Llama 3 70B │    │  FAISS Dense + BM25 Sparse + Reranker│
└─────────────┘    │  10,000+ legal chunks indexed        │
                   └──────────────────────────────────────┘
                               │
                   ┌───────────┴──────────────┐
                   ▼                          ▼
            ┌─────────────┐         ┌──────────────────┐
            │  MongoDB    │         │  Legal Knowledge  │
            │  (Beanie)   │         │  Constitution     │
            └─────────────┘         │  IPC/BNS, CrPC   │
                                    │  Labour Codes     │
                                    │  RTI Act          │
                                    │  800+ Schemes     │
                                    └──────────────────┘
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (free)
- Groq API key (free at console.groq.com)
- Node.js 18+ (optional, for frontend dev)

### 1. Clone the repo
```bash
git clone https://github.com/Kartavyasonar/nyaya-ai.git
cd nyaya-ai
```

### 2. Backend setup
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys (see Environment Variables section below)
```

### 3. Start backend
```bash
python main.py
# API docs at: http://localhost:8000/api/docs
```

### 4. Frontend
```bash
# Serve index.html directly — no build needed
# Option A: VS Code Live Server
# Option B: Python
cd frontend
python -m http.server 3000
# Open: http://localhost:3000
```

---

## 🔑 Environment Variables

Edit `backend/.env`:

```env
# Required
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/nyaya_ai
GROQ_API_KEY=your_groq_key_here        # Free: console.groq.com

# Optional (for WhatsApp bot)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Auto-generated on first run
JWT_SECRET=change_this_to_random_string
SECRET_KEY=change_this_to_random_string
```

---

## ☁️ Deploy to Production

### Backend → Render (Free)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect GitHub repo
4. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Region:** Singapore (closest to India)
5. Add Environment Variables (from .env)
6. Deploy ✅

### Frontend → Vercel (Free)

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import GitHub repo
3. Settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Other
   - **Build Command:** *(leave empty)*
   - **Output Directory:** `.`
4. Add environment variable:
   - `VITE_API_URL` = your Render backend URL
5. Deploy ✅

### Update API URL in frontend
In `frontend/index.html`, find:
```javascript
const API_BASE = '/api/v1';
```
Change to your Render URL:
```javascript
const API_BASE = 'https://nyaya-ai-backend.onrender.com/api/v1';
```

---

## 📱 WhatsApp Bot Setup

1. Create [Twilio account](https://twilio.com) (free $15 credit)
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Join sandbox by sending "join [word]" to the sandbox number
4. Set webhook URL to: `https://your-backend.onrender.com/api/v1/whatsapp/webhook`
5. Users can now WhatsApp your Twilio number and get legal help

---

## 📚 Legal Knowledge Base

The RAG index covers:
| Source | Coverage |
|---|---|
| Constitution of India | All 395 Articles + Amendments |
| BNS/IPC 2023 | All 358 Sections |
| BNSS/CrPC 2023 | All 531 Sections |
| Labour Codes 2020 | All 4 codes |
| RTI Act 2005 | Complete with procedures |
| Consumer Protection Act 2019 | Full coverage |
| POCSO, DV Act, Dowry Act | Full coverage |
| Forest Rights Act 2006 | Full coverage |
| Government Schemes | 800+ schemes |
| SC Judgments | Key landmarks |
| Helplines | All national helplines |

---

## 🤝 Contributing

This is an open-source project for public good.

1. Fork the repo
2. Add more legal knowledge to `backend/rag/data_loader.py`
3. Add support for more Indian languages
4. Improve the UI
5. Submit PR

**Priority contributions needed:**
- State-specific tenancy laws (42 states)
- More SC/HC judgments
- Voice support improvements
- Offline PWA support

---

## 📄 License

MIT License — Free to use, modify, distribute.

**This project is dedicated to every Indian who ever couldn't afford a lawyer.**

---

## 🆘 Emergency Helplines

| Helpline | Number |
|---|---|
| Emergency | 112 |
| Police | 100 |
| Women Helpline | 181 |
| Child Helpline | 1098 |
| **Free Legal Aid (NALSA)** | **15100** |
| Cyber Crime | 1930 |
| Consumer | 14404 |

---

*Built by [Kartavya Sonar](https://kartavyasonar.github.io) — MSc Computer Science, University of Leeds*

