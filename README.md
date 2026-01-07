# EmailCraft AI

A production-ready, multi-agent AI system for generating high-conversion B2B outreach emails using Groq-powered LLMs, RAG (Retrieval-Augmented Generation), intelligent persona analysis, and research-backed best practices.

**Built on proven B2B email research** - implements industry standards for subject lines, length, personalization, and tone based on analysis of successful outreach campaigns.

## 🤖 Why This is an AI Agent System (Not a Chatbot)

This system is fundamentally different from a chatbot:

- **Goal-Driven**: Executes a specific workflow (email generation) rather than conversational interaction
- **Multi-Agent Architecture**: Uses specialized agents that work together autonomously
- **Self-Evaluating**: The Evaluation Agent critiques and optimizes its own output
- **RAG-Enhanced**: Uses real vector database retrieval, not just prompt engineering
- **Deterministic Flow**: Follows a structured pipeline: Persona → Retrieval → Generation → Evaluation
- **Autonomous Optimization**: Automatically improves output quality when below threshold

## 🚀 Why Groq?

- **Speed**: Ultra-fast inference (8B model in milliseconds)
- **Cost-Effective**: Significantly cheaper than alternatives
- **Quality**: Llama 3.1 models provide excellent output quality
- **Scalability**: Can handle high-volume requests efficiently

## 🏗️ Architecture

```
User Input
    ↓
Planner Agent (Orchestrator)
    ├─ IF job_url provided → Job Scraping Agent
    └─ ELSE → Use structured business input
    ↓
┌─────────────────────────────────────┐
│ 1. Persona Analyzer Agent           │
│    → Analyzes role, industry, needs │
│    → Uses scraped job data if available │
│    → Outputs structured JSON        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Template Retrieval Agent (RAG)   │
│    → ChromaDB vector search         │
│    → Retrieves top-K templates      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Email Generation Agent           │
│    → Combines persona + templates   │
│    → Generates personalized email   │
│    → Avoids spam triggers           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. Evaluation & Optimization Agent  │
│    → Self-critique (5 metrics)       │
│    → Optimizes if score < 8.0       │
│    → Generates alternative subjects  │
└─────────────────────────────────────┘
    ↓
Final Optimized Email + Quality Metrics
```

## 📁 Project Structure

```
cold_outreach_ai_agent/
│
├── main.py                     # FastAPI backend + static frontend serving
├── Dockerfile                  # Docker configuration for deployment
├── render.yaml                 # Render deployment configuration
│
├── frontend/                   # Custom HTML/CSS/JS Frontend
│   ├── index.html              # Main UI
│   ├── styles.css              # Styling
│   └── script.js               # Frontend logic
│
├── agents/                     # Multi-agent system
│   ├── __init__.py
│   ├── planner_agent.py        # Orchestrator (main workflow)
│   ├── persona_agent.py        # Persona analysis
│   ├── retrieval_agent.py      # Template retrieval (RAG)
│   ├── portfolio_agent.py      # Portfolio matching (RAG)
│   ├── generation_agent.py     # Email generation
│   └── evaluation_agent.py     # Evaluation & optimization
│
├── prompts/                    # LLM prompts (research-backed)
│   ├── persona_prompt.txt      # Persona analysis
│   ├── generation_prompt.txt   # Email generation (B2B best practices)
│   ├── evaluation_prompt.txt   # Quality evaluation (5 metrics)
│   └── optimization_prompt.txt # Email optimization
│
├── models/                     # Pydantic schemas
│   ├── __init__.py
│   └── schemas.py              # All data models
│
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── groq_client.py          # Central Groq LLM client
│   └── chroma_utils.py         # ChromaDB helpers
│
├── database/                   # Analytics database
│   ├── __init__.py
│   └── db_manager.py           # SQLite database manager
│
├── data/                       # Data files
│   ├── email_templates.json    # Email template database
│   ├── my_portfolio.csv        # Your portfolio (customize this!)
│   └── portfolio.json          # Portfolio metadata
│
├── vectorstore/                # Vector databases
│   └── chroma_db/              # ChromaDB persistence
│
├── .github/                    # GitHub Actions CI/CD
│   └── workflows/
│       └── ci-cd.yml           # CI/CD pipeline
│
├── .env                        # Environment variables (create this!)
├── .gitignore
├── requirements.txt            # Python dependencies
├── start_backend.bat           # Windows: Start server
└── README.md                   # This file
```

## 🛠️ Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd cold_outreach_ai_agent
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the root directory:

   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.1-8b-instant
   ```

5. **Initialize ChromaDB** (automatic on first run)

   The system will automatically create and populate the vector database on first use.

## 🚀 Usage

### Local Development

1. **Start the server**:

   ```bash
   python main.py
   ```

   Or:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

2. **Open browser** to `http://localhost:8000`

### Features

#### New Email Tab

- Generate single personalized cold emails
- Option to provide job posting URL for enhanced personalization
- Real-time quality evaluation with 5 metrics
- Alternative subject line suggestions
- Strengths and improvement suggestions

#### Batch Emails Tab

- Upload CSV with multiple prospects
- Process all emails automatically
- View individual results with full evaluation
- Download results as Excel file

#### History Tab

- View all generated emails
- Search and filter by company/role
- Re-use successful templates

#### Analytics Tab

- Email generation statistics
- Quality score trends
- Performance insights

## 🎯 Agent Responsibilities

### 1. Planner Agent

- Orchestrates the entire pipeline
- Controls execution flow based on input type
- Manages agent communication
- Returns structured results

### 2. Persona Analyzer Agent

- Analyzes target recipient persona
- Infers pain points and decision drivers
- Determines communication style
- Outputs structured JSON insights

### 3. Template Retrieval Agent (RAG)

- Uses ChromaDB for vector storage
- Performs semantic similarity search
- Retrieves top-K relevant templates

### 4. Portfolio Agent (RAG)

- Matches relevant portfolio items
- Uses keyword-based filtering
- Returns projects that demonstrate capabilities

### 5. Email Generation Agent

- Combines persona insights + templates
- Generates subject line, body, CTA
- Avoids spam trigger words
- Ensures personalization

### 6. Evaluation & Optimization Agent

- Self-critiques email quality
- Evaluates 5 metrics (clarity, tone, length, spam risk, personalization)
- Optimizes if score < 6.5
- Generates alternative subject lines

## 📊 Evaluation Metrics

The system evaluates emails on 5 metrics (research-backed):

| Metric          | Weight | Description                           |
| --------------- | ------ | ------------------------------------- |
| Clarity         | 25%    | Message clarity and value proposition |
| Tone            | 20%    | Match with B2B professional standards |
| Length          | 15%    | Optimal email length (100-150 words)  |
| Spam Risk       | 15%    | Avoidance of spam triggers            |
| Personalization | 25%    | Specific references to role/company   |

**Score Meanings:**

- **8.5+** → Excellent, ready to send
- **7.0-8.4** → Good, minor improvements possible
- **<6.5** → Triggers auto-optimization

## 🌐 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions including:

- Docker deployment
- Render deployment
- GitHub Actions CI/CD setup

## 🔧 Configuration

### Groq Models

Set in `.env`:

```env
GROQ_MODEL=llama-3.1-8b-instant
```

### Quality Threshold

Adjust in `agents/evaluation_agent.py`:

```python
QUALITY_THRESHOLD = 6.5  # Only optimize very low scores
```

### RAG Parameters

Adjust in `agents/retrieval_agent.py`:

```python
top_k = 3  # Number of templates to retrieve
```

## 📝 Adding Custom Templates

Edit `data/email_templates.json` to add your own templates:

```json
{
  "id": "unique_id",
  "title": "Template name",
  "industry": "Target industry",
  "use_case": "Use case description",
  "subject_line": "Subject template",
  "body": "Email body template",
  "cta": "Call-to-action",
  "performance_score": 8.5
}
```

## 🔒 Security Notes

- Never commit `.env` file with API keys
- In production, restrict CORS origins in `main.py`
- Use environment variables for all secrets

## 🐛 Troubleshooting

**ChromaDB initialization errors:**

- Ensure `vectorstore/chroma_db` directory exists
- Check write permissions

**Groq API errors:**

- Verify `GROQ_API_KEY` in `.env`
- Check API quota/limits

**Import errors:**

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

## 📄 License

MIT License - feel free to use for commercial projects.

## 🤝 Contributing

Contributions welcome! Please ensure:

- Code follows existing structure
- All agents remain modular
- Documentation updated

---

**Built with ❤️ using Groq, LangChain, and ChromaDB**
