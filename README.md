# EmailCraft AI 🚀

<div align="center">

![EmailCraft AI Banner](assets/banner.png)

**A production-ready, multi-agent AI system for generating high-conversion B2B cold outreach emails**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-EmailCraft%20AI-blue?style=for-the-badge)](https://emailcraft-ai.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[🌐 Live Demo](https://emailcraft-ai.onrender.com) • [📖 Documentation](#-features) • [🚀 Quick Start](#-quick-start) • [🎥 Video Demo](#-demo)

</div>

---

## 🎥 Demo

<!-- Add your video link here -->

[![EmailCraft AI Demo](assets/video-thumbnail.png)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

> Click to watch the full demo video

---

## 📸 Screenshots

<div align="center">

### Landing Page

![Landing Page](assets/screenshots/landing-page.png)

### Email Generation

![Generate Email](assets/screenshots/generate-email.png)

### Batch Processing

![Batch Emails](assets/screenshots/batch-emails.png)

### Analytics Dashboard

![Analytics Dashboard](assets/screenshots/dashboard.png)

</div>

---

## ✨ Features

| Feature                       | Description                                                             |
| ----------------------------- | ----------------------------------------------------------------------- |
| 🤖 **Multi-Agent AI**         | 6 specialized agents working together autonomously                      |
| 📧 **Smart Email Generation** | Context-aware personalized cold emails                                  |
| 🔗 **Job URL Scraping**       | Auto-extract role details from LinkedIn/job postings                    |
| 📊 **Quality Scoring**        | 5-metric evaluation (Clarity, Tone, Length, Spam Risk, Personalization) |
| 💼 **Portfolio Matching**     | RAG-based portfolio recommendation                                      |
| 📈 **Analytics Dashboard**    | Track performance, scores, and trends                                   |
| 📁 **Batch Processing**       | Process 10-50+ emails from CSV                                          |
| 📥 **Excel Export**           | Export results with full details                                        |
| 🌐 **Production Ready**       | Deployed on Render with PostgreSQL & Pinecone                           |

---

## 🤖 Why This is an AI Agent System

This is **NOT a chatbot** - it's an autonomous agent system:

- **Goal-Driven**: Executes a specific workflow, not conversations
- **Multi-Agent**: 6 specialized agents collaborate autonomously
- **Self-Evaluating**: Critiques and optimizes its own output
- **RAG-Enhanced**: Real vector database retrieval, not just prompts
- **Deterministic**: Follows structured pipeline with consistent results

---

## 🏗️ Architecture

```
User Input (Job URL or Role/Industry)
    ↓
┌─────────────────────────────────────┐
│        Planner Agent                │
│     (Orchestrates Pipeline)         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│     Job Scraper Agent (Optional)    │
│  → Extracts role, skills, company   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│       Persona Analyzer Agent        │
│  → Analyzes pain points, needs      │
│  → Determines communication style   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│    Template Retrieval Agent (RAG)   │
│  → ChromaDB/Pinecone vector search  │
│  → Retrieves top-3 templates        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│      Portfolio Agent (RAG)          │
│  → Matches relevant projects        │
│  → Returns portfolio links          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│      Email Generation Agent         │
│  → Combines persona + templates     │
│  → Generates personalized email     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   Evaluation & Optimization Agent   │
│  → Scores on 5 metrics              │
│  → Auto-optimizes if score < 6.5    │
│  → Generates alt subject lines      │
└─────────────────────────────────────┘
    ↓
Final Email + Quality Metrics + Portfolio Links
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Groq API Key](https://console.groq.com) (free)

### Installation

```bash
# Clone the repository
git clone https://github.com/07fahim/EmailCraft-AI.git
cd EmailCraft-AI

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### Run Locally

```bash
python main.py
```

Open browser: `http://localhost:8000`

---

## 📁 Project Structure

```
EmailCraft-AI/
├── main.py                     # FastAPI backend
├── Dockerfile                  # Docker configuration
├── render.yaml                 # Render deployment
│
├── frontend/                   # Web UI
│   ├── index.html
│   ├── styles.css
│   └── script.js
│
├── agents/                     # AI Agents
│   ├── planner_agent.py        # Orchestrator
│   ├── scraper_agent.py        # Job URL scraping
│   ├── persona_agent.py        # Persona analysis
│   ├── retrieval_agent.py      # Template RAG
│   ├── portfolio_agent.py      # Portfolio RAG
│   ├── generation_agent.py     # Email generation
│   └── evaluation_agent.py     # Quality scoring
│
├── prompts/                    # LLM Prompts
│   ├── persona_prompt.txt
│   ├── generation_prompt.txt
│   ├── evaluation_prompt.txt
│   └── optimization_prompt.txt
│
├── utils/                      # Utilities
│   ├── groq_client.py          # LLM client (rate-limited)
│   ├── vector_store.py         # ChromaDB/Pinecone
│   └── batch_processor.py      # Batch email processing
│
├── database/                   # Database
│   ├── db_manager.py           # SQLite/PostgreSQL
│   └── models.py               # SQLAlchemy models
│
├── data/                       # Data files
│   ├── email_templates.json    # Email templates
│   └── my_portfolio.csv        # Your portfolio
│
└── assets/                     # Images & media
    └── screenshots/
```

---

## 📊 Quality Metrics

Emails are evaluated on 5 research-backed metrics:

| Metric              | Weight | Description             |
| ------------------- | ------ | ----------------------- |
| **Clarity**         | 25%    | Clear value proposition |
| **Tone**            | 20%    | Professional B2B tone   |
| **Length**          | 15%    | Optimal 100-150 words   |
| **Spam Risk**       | 15%    | Avoids spam triggers    |
| **Personalization** | 25%    | Role/company references |

**Score Interpretation:**

- **8.5+** → Excellent, ready to send ✅
- **7.0-8.4** → Good, minor tweaks possible
- **< 6.5** → Auto-optimization triggered 🔄

---

## 🌐 Deployment

### Dual-Mode Architecture

EmailCraft AI features a **smart dual-mode architecture** that automatically detects your environment:

| Component           | 🖥️ Local Development  | ☁️ Production (Render)       |
| ------------------- | --------------------- | ---------------------------- |
| **Database**        | SQLite (zero config)  | PostgreSQL (Supabase)        |
| **Vector Store**    | ChromaDB (local)      | Pinecone (cloud)             |
| **Embeddings**      | sentence-transformers | Pinecone Inference API       |
| **Embedding Model** | all-MiniLM-L6-v2      | multilingual-e5-large        |
| **Hosting**         | localhost:8000        | Render Docker                |
| **Batch Delay**     | 2 seconds             | 30 seconds (rate limit safe) |

---

### 🖥️ Local Development Setup

**What you need:**

- Python 3.11+
- Groq API key only (free at [console.groq.com](https://console.groq.com))

**What you get:**

- SQLite database (auto-created)
- ChromaDB vector store (local embeddings)
- Fast 2-second batch delay

```bash
# 1. Clone and setup
git clone https://github.com/07fahim/EmailCraft-AI.git
cd EmailCraft-AI
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
echo GROQ_API_KEY=your_groq_key_here > .env

# 4. Run!
python main.py
```

Open: `http://localhost:8000` ✅

---

### ☁️ Production Setup (Render)

**What you need:**
| Service | Purpose | Sign Up |
|---------|---------|---------|
| **Groq** | LLM API | [console.groq.com](https://console.groq.com) |
| **Pinecone** | Vector database | [pinecone.io](https://www.pinecone.io) |
| **Supabase** | PostgreSQL database | [supabase.com](https://supabase.com) |
| **Render** | Hosting | [render.com](https://render.com) |

**Step 1: Pinecone Setup**

1. Create account at [pinecone.io](https://www.pinecone.io)
2. Create index: `email-templates` (768 dimensions, cosine)
3. Get API key from dashboard

**Step 2: Supabase Setup**

1. Create project at [supabase.com](https://supabase.com)
2. Go to Settings → Database → Connection String (URI)
3. Copy the PostgreSQL URL

**Step 3: Render Deploy**

1. Fork this repository
2. Connect to [Render](https://render.com)
3. Create **Web Service** → Select Docker
4. Set environment variables:

| Variable               | Value                        | Required |
| ---------------------- | ---------------------------- | -------- |
| `GROQ_API_KEY`         | Your Groq API key            | ✅       |
| `PINECONE_API_KEY`     | Your Pinecone API key        | ✅       |
| `PINECONE_ENVIRONMENT` | `us-east-1` (or your region) | ✅       |
| `DATABASE_URL`         | Supabase PostgreSQL URL      | ✅       |
| `GROQ_MODEL`           | `llama-3.1-8b-instant`       | ❌       |

5. Deploy! 🚀

---

### Auto-Detection Logic

The app automatically switches modes based on environment variables:

```python
# Production mode if either is set:
if PINECONE_API_KEY:
    → Use Pinecone + Pinecone Inference embeddings
    → Use 30-second batch delay

if DATABASE_URL:
    → Use PostgreSQL

# Otherwise:
    → Use ChromaDB + sentence-transformers
    → Use SQLite
    → Use 2-second batch delay
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete step-by-step deployment guide.

---

## 🔧 Configuration

### Environment Variables

| Variable           | Required | Default                | Description           |
| ------------------ | -------- | ---------------------- | --------------------- |
| `GROQ_API_KEY`     | ✅       | -                      | Groq API key          |
| `GROQ_MODEL`       | ❌       | `llama-3.1-8b-instant` | LLM model             |
| `PINECONE_API_KEY` | ❌       | -                      | Pinecone (production) |
| `DATABASE_URL`     | ❌       | -                      | PostgreSQL URL        |

### Customize Portfolio

Edit `data/my_portfolio.csv`:

```csv
tech_stack,link
"React, Node.js, MongoDB",https://github.com/you/project1
"Python, TensorFlow, NLP",https://github.com/you/project2
```

### Customize Templates

Edit `data/email_templates.json`:

```json
{
  "id": "unique_id",
  "title": "Template Name",
  "industry": "Technology",
  "subject_line": "Subject template",
  "body": "Email body template",
  "performance_score": 8.5
}
```

---

## 🐛 Troubleshooting

| Issue                       | Solution                                             |
| --------------------------- | ---------------------------------------------------- |
| **Rate limit errors (429)** | Batch processing uses 30s delay in production        |
| **ChromaDB errors**         | Ensure `vectorstore/` directory exists               |
| **Import errors**           | Activate venv, run `pip install -r requirements.txt` |
| **Groq API errors**         | Check API key and quota at console.groq.com          |

---

## 🛣️ Roadmap

- [ ] Email A/B testing
- [ ] CRM integrations (HubSpot, Salesforce)
- [ ] Custom model fine-tuning
- [ ] Email scheduling
- [ ] Team collaboration features

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - feel free to use for commercial projects.

---

## 🙏 Acknowledgments

- **Groq** - Ultra-fast LLM inference
- **LangChain** - LLM orchestration
- **ChromaDB & Pinecone** - Vector databases
- **FastAPI** - Modern Python web framework

---

<div align="center">

**Built with ❤️ by [Fahim](https://github.com/07fahim)**

⭐ Star this repo if you find it helpful!

</div>
