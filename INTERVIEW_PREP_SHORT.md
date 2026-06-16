# EmailCraft AI - Quick Interview Prep

## 🎯 30-Second Pitch

"I built a multi-agent AI system that automates B2B cold email generation. It uses 6 specialized agents in a pipeline - scraping jobs, analyzing personas, matching templates and portfolio items using RAG, generating emails, and evaluating quality. It includes batch processing, automated lead sourcing from Google Maps, and a full analytics dashboard. Built with FastAPI, deployed on Render, with caching and rate limiting for production use."

---

## 🤖 The 6 Agents (Know These!)

1. **Planner** - Orchestrates the pipeline
2. **Scraper** - Extracts job details from URLs (24hr cache)
3. **Persona** - Analyzes recipient psychology & pain points
4. **Template Retrieval** - RAG search for relevant email templates
5. **Portfolio** - RAG search for matching projects
6. **Evaluation** - Scores quality (5 metrics), auto-optimizes if < 6.5

---

## 🔄 3 Workflows

**Single Email**: Job URL → 6 agents → Email (20-30s)
**Batch**: CSV upload → Process each row → Export Excel (30s/email)
**Lead Gen**: Google Maps scrape → Generate email per lead → Export (30s/lead)

---

## 💻 Tech Stack

**Backend**: FastAPI, LangChain, Groq (llama-3.1-8b-instant)
**AI/ML**: ChromaDB (local), Pinecone (prod), RAG with embeddings
**Database**: SQLite (local), PostgreSQL (prod) - auto-switches
**Frontend**: Vanilla JS, CSS3, no frameworks
**Deploy**: Render.com, Docker, Supabase

---

## 🚀 Key Optimizations

1. **Caching** - 1hr TTL, reduces API calls 60%
2. **Rate Limiting** - 1.5s between calls, prevents 429 errors
3. **Pre-compiled Regex** - 30% faster JSON parsing
4. **Smart Optimization** - Only optimizes scores < 6.5
5. **Lazy Loading** - Agents initialize on first use

---

## 🎤 Top 5 Interview Questions

### Q1: Why is this an "agent system"?

**A**: "It's goal-driven, not conversational. 6 specialized agents work autonomously in a pipeline. Each has one job, they collaborate without human intervention, and the system self-evaluates and optimizes."

### Q2: What's RAG?

**A**: "Retrieval-Augmented Generation. Instead of relying only on LLM training data, I retrieve relevant templates and portfolio items from a vector database using semantic similarity search. This grounds the output in real data."

### Q3: Biggest challenge?

**A**: "Making LLM output consistent. LLMs sometimes return malformed JSON. I solved it with pre-compiled regex, strong format instructions, lower temperature (0.5), and fallback templates."

### Q4: How would you scale?

**A**: "Already production-ready: caching (60% reduction), PostgreSQL (millions of records), Pinecone (cloud vector DB), rate limiting, and could add Celery for async processing."

### Q5: Why FastAPI over Flask?

**A**: "Faster, type-safe with Pydantic, auto-documentation, native async support, and better developer experience."

---

## 📊 Quality Metrics (5 Scores)

1. **Clarity** (25%) - Clear value proposition
2. **Personalization** (25%) - Company/role references
3. **Tone** (20%) - Professional
4. **Length** (15%) - 80-180 words optimal
5. **Spam Risk** (15%) - Avoids triggers

Weighted average → Overall score (0-10)

---

## 🎯 Demo Flow (2 minutes)

1. **Show landing page** (5s)
2. **Generate single email** (60s)
   - Paste job URL
   - Show loading animation (agents working)
   - Highlight: Score 8.7, portfolio matched, alt subjects
3. **Show analytics** (30s)
   - Total emails, avg score, distribution
4. **Optional: Lead generation** (30s)
   - "software companies in San Francisco"
   - Shows scraped leads + generated emails

---

## 💡 Impressive Details to Mention

- "Thread-safe rate limiter prevents API errors"
- "MD5 hashing for fast cache lookups"
- "Zero code changes between local and production"
- "Self-correcting evaluation - keeps better version"
- "Frontend has zero dependencies, loads in <100ms"
- "Semantic similarity search with vector embeddings"

---

## 🚨 Honest Weaknesses

1. **No auth** - Would add JWT for multi-user
2. **No automated tests** - Would add pytest
3. **No email sending** - Would integrate SendGrid
4. **English only** - Would add i18n
5. **No retry logic** - Would add fallbacks

---

## 📝 Code to Show (If Asked)

**Show `planner_agent.py`**:

- Clean agent orchestration
- Error handling (don't fail on DB errors)
- Performance tracking

**Show `main.py`**:

- Caching implementation
- Rate limiting
- Clean API design

---

## ✅ Must Know

- [ ] Explain 6 agents in 30 seconds
- [ ] What is RAG and why you used it
- [ ] Difference from ChatGPT (goal-driven vs conversational)
- [ ] Caching strategy (1hr TTL, MD5 keys)
- [ ] How evaluation works (5 metrics, auto-optimize)
- [ ] Tech stack reasoning (FastAPI, vanilla JS)
- [ ] Scaling approach (already production-ready)

---

## 🎬 Closing Statement

"EmailCraft AI shows I can build production-ready AI systems - not just demos. It has proper architecture, caching, error handling, database integration, and deployment. The multi-agent design demonstrates I can break complex problems into manageable pieces and orchestrate them effectively. It's fully functional and ready for real-world use."

---

**Time to prepare: 30 minutes**
**Focus on: 6 agents, RAG, optimizations, demo flow**
**Be ready to: Explain technical decisions, discuss scaling, show code**

Good luck! 🚀
