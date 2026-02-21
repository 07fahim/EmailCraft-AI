# EmailCraft AI

**A production-ready, multi-agent AI system for generating high-conversion B2B cold outreach emails**

[![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

[📖 User Guide](USER_GUIDE.md) • [🚀 Quick Start](#quick-start) • [🎯 Lead Sourcing](LEAD_SOURCING_GUIDE.md) • [📝 Custom Templates](CUSTOM_TEMPLATES_GUIDE.md)

---

## Screenshots

### Landing Page

![Landing Page](assets/screenshots/landing-page.png)

### Main Application

![Main Interface](assets/screenshots/main-interface.png)

### Email Generation

![Single Email Result](assets/screenshots/single-email-result.png)

### Lead Generation

![Lead Generation Results](assets/screenshots/lead-gen-results.png)

### Analytics Dashboard

![Analytics Dashboard](assets/screenshots/analytics-dashboard.png)

_See [User Guide](USER_GUIDE.md) for complete documentation_

---

## Features

| Feature                    | Description                                                                    |
| -------------------------- | ------------------------------------------------------------------------------ |
| **Multi-Agent AI**         | 6 specialized agents working together autonomously                             |
| **Lead Sourcing**          | Automated Google Maps scraping + email discovery                               |
| **Smart Email Generation** | Context-aware personalized cold emails                                         |
| **Job URL Scraping**       | Auto-extract role details from LinkedIn/job postings                           |
| **Quality Scoring**        | 5-metric evaluation system (Clarity, Tone, Length, Spam Risk, Personalization) |
| **Portfolio Matching**     | RAG-based portfolio recommendation                                             |
| **Analytics Dashboard**    | Track performance, scores, and trends                                          |
| **Batch Processing**       | Process 10-50+ emails from CSV                                                 |
| **Excel Export**           | Export results with full details                                               |
| **Light/Dark Mode**        | Beautiful UI with theme switching                                              |

---

## Why This is an AI Agent System

This is not a chatbot - it's an autonomous multi-agent system:

- **Goal-Driven**: Executes specific workflows, not conversations
- **Multi-Agent**: 6 specialized agents collaborate autonomously
- **Self-Evaluating**: Critiques and optimizes its own output
- **RAG-Enhanced**: Real vector database retrieval for templates and portfolio
- **Deterministic**: Follows structured pipeline with consistent results

---

## Theme System

EmailCraft AI features beautiful light and dark modes with automatic theme detection:

**Light Mode**: Professional purple (#744B93) and white - perfect for daytime use
**Dark Mode**: Dark navy (#0f172a) with bright purple (#a78bfa) - perfect for nighttime use

Features:

- Automatic detection based on system preference
- Persistent theme choice
- Smooth 0.3s color transitions
- Works across all pages
- High contrast ratios for accessibility

Toggle theme using the moon/sun icon in the navbar.

---

## Automated Lead Sourcing

EmailCraft AI includes fully automated lead generation that finds businesses and generates personalized emails in one workflow.

### How It Works

```
Search Criteria (Business Type + Location)
    ↓
Lead Sourcing Agent
  → Scrapes Google Maps via Apify
  → Finds businesses with websites
    ↓
Email Generation Pipeline
  → 6-agent system generates email
  → Personalized for each lead
    ↓
Ready-to-Send Outreach Emails
```

### Setup

**Get API Key:**

| Service   | Purpose              | Sign Up                        |
| --------- | -------------------- | ------------------------------ |
| **Apify** | Google Maps scraping | [apify.com](https://apify.com) |

**Add to .env:**

```env
APIFY_API_KEY=your_apify_api_key_here
```

### Usage

**Via Web UI:**

1. Go to "Lead Generation" tab
2. Enter business type (e.g., "software companies")
3. Enter location (e.g., "San Francisco, CA")
4. Set number of leads (5-50)
5. Click "Generate Leads & Emails"

**Via API:**

```bash
curl -X POST http://localhost:8000/generate-from-leads \
  -H "Content-Type: application/json" \
  -d '{
    "business_type": "software companies",
    "location": "San Francisco, CA",
    "max_results": 20,
    "sender_name": "Alex",
    "sender_company": "TechSolutions",
    "sender_services": "AI development and consulting"
  }'
```

### What You Get

For each lead:

- Company name, website, phone, address
- Personalized cold email (subject + body + CTA)
- Quality score (0-10)
- Export to Excel/CSV

**Note:** Email addresses are not automatically found. You can manually add them or use external email finder tools.

---

## Architecture

### Email Generation Pipeline

```
User Input (Job URL or Role/Industry)
    ↓
Planner Agent (Orchestrates Pipeline)
    ↓
Job Scraper Agent (Optional)
  → Extracts role, skills, company
    ↓
Persona Analyzer Agent
  → Analyzes pain points, needs
  → Determines communication style
    ↓
Template Retrieval Agent (RAG)
  → ChromaDB/Pinecone vector search
  → Retrieves top-3 templates
    ↓
Portfolio Agent (RAG)
  → Matches relevant projects
  → Returns portfolio links
    ↓
Email Generation Agent
  → Combines persona + templates
  → Generates personalized email
    ↓
Evaluation & Optimization Agent
  → Scores on 5 metrics
  → Auto-optimizes if score < 6.5
  → Generates alt subject lines
    ↓
Final Email + Quality Metrics + Portfolio Links
```

### Lead Generation Pipeline

```
Search Criteria (Business Type + Location)
    ↓
Lead Sourcing Agent
  → Scrapes Google Maps (Apify)
  → Returns enriched lead data
    ↓
For Each Lead:
  → Standard Email Generation Pipeline (above)
    ↓
Batch of Ready-to-Send Emails
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Groq API Key](https://console.groq.com) (free)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/EmailCraft-AI.git
cd EmailCraft-AI

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
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

### Run

```bash
python main.py
```

Open browser: `http://localhost:8000`

---

## Project Structure

```
EmailCraft-AI/
├── main.py                     # FastAPI backend
├── Dockerfile                  # Docker configuration
├── render.yaml                 # Render deployment
│
├── frontend/                   # Web UI
│   ├── index.html
│   ├── landing.html
│   ├── styles.css
│   └── script.js
│
├── agents/                     # AI Agents
│   ├── planner_agent.py        # Orchestrator
│   ├── scraper_agent.py        # Job URL scraping
│   ├── lead_sourcing_agent.py  # Google Maps + Email discovery
│   ├── persona_agent.py        # Persona analysis
│   ├── retrieval_agent.py      # Template RAG
│   ├── portfolio_agent.py      # Portfolio RAG
│   ├── generation_agent.py     # Email generation
│   └── evaluation_agent.py     # Quality scoring
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

## Quality Metrics

Emails are evaluated on 5 research-backed metrics:

| Metric              | Weight | Description             |
| ------------------- | ------ | ----------------------- |
| **Clarity**         | 25%    | Clear value proposition |
| **Tone**            | 20%    | Professional B2B tone   |
| **Length**          | 15%    | Optimal 100-150 words   |
| **Spam Risk**       | 15%    | Avoids spam triggers    |
| **Personalization** | 25%    | Role/company references |

**Score Interpretation:**

- **8.5+** → Excellent, ready to send
- **7.0-8.4** → Good, minor tweaks possible
- **< 6.5** → Auto-optimization triggered

---

## Deployment

### Dual-Mode Architecture

EmailCraft AI automatically detects your environment and switches between local and production modes:

| Component        | Local Development     | Production (Render)          |
| ---------------- | --------------------- | ---------------------------- |
| **Database**     | SQLite (zero config)  | PostgreSQL (Supabase)        |
| **Vector Store** | ChromaDB (local)      | Pinecone (cloud)             |
| **Embeddings**   | sentence-transformers | Pinecone Inference API       |
| **Batch Delay**  | 2 seconds             | 30 seconds (rate limit safe) |

### Local Development

**Requirements:**

- Python 3.11+
- Groq API key only

**Setup:**

```bash
git clone https://github.com/yourusername/EmailCraft-AI.git
cd EmailCraft-AI
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
echo GROQ_API_KEY=your_key > .env
python main.py
```

### Production Setup (Render)

**Required Services:**

| Service      | Purpose             | Sign Up                                      |
| ------------ | ------------------- | -------------------------------------------- |
| **Groq**     | LLM API             | [console.groq.com](https://console.groq.com) |
| **Pinecone** | Vector database     | [pinecone.io](https://www.pinecone.io)       |
| **Supabase** | PostgreSQL database | [supabase.com](https://supabase.com)         |
| **Render**   | Hosting             | [render.com](https://render.com)             |

**Environment Variables:**

| Variable               | Required | Description                       |
| ---------------------- | -------- | --------------------------------- |
| `GROQ_API_KEY`         | ✅       | Your Groq API key                 |
| `PINECONE_API_KEY`     | ✅       | Your Pinecone API key             |
| `PINECONE_ENVIRONMENT` | ✅       | Pinecone region (e.g., us-east-1) |
| `DATABASE_URL`         | ✅       | Supabase PostgreSQL URL           |
| `GROQ_MODEL`           | ❌       | Default: llama-3.1-8b-instant     |

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete step-by-step guide.

---

## Configuration

### Environment Variables

| Variable           | Required | Default              | Description           |
| ------------------ | -------- | -------------------- | --------------------- |
| `GROQ_API_KEY`     | ✅       | -                    | Groq API key          |
| `GROQ_MODEL`       | ❌       | llama-3.1-8b-instant | LLM model             |
| `PINECONE_API_KEY` | ❌       | -                    | Pinecone (production) |
| `DATABASE_URL`     | ❌       | -                    | PostgreSQL URL        |
| `APIFY_API_KEY`    | ❌       | -                    | Google Maps scraping  |
| `ANYMAIL_API_KEY`  | ❌       | -                    | Email discovery       |

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

See [Custom Templates Guide](CUSTOM_TEMPLATES_GUIDE.md) for details.

---

## Troubleshooting

| Issue                       | Solution                                             |
| --------------------------- | ---------------------------------------------------- |
| **Rate limit errors (429)** | Batch processing uses 30s delay in production        |
| **ChromaDB errors**         | Ensure `vectorstore/` directory exists               |
| **Import errors**           | Activate venv, run `pip install -r requirements.txt` |
| **Groq API errors**         | Check API key and quota at console.groq.com          |

---

## Documentation

- [User Guide](USER_GUIDE.md) - Complete user manual
- [Lead Sourcing Guide](LEAD_SOURCING_GUIDE.md) - Automated lead generation
- [Custom Templates Guide](CUSTOM_TEMPLATES_GUIDE.md) - Template customization
- [Deployment Guide](DEPLOYMENT.md) - Production deployment

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - feel free to use for commercial projects.

---

## Acknowledgments

- **Groq** - Ultra-fast LLM inference
- **LangChain** - LLM orchestration
- **ChromaDB & Pinecone** - Vector databases
- **FastAPI** - Modern Python web framework

---

**Built with ❤️ by developers, for developers**

⭐ Star this repo if you find it helpful!
