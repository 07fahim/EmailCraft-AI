# 🐛 Debugging Cold Outreach AI with LangSmith

This guide helps you debug common issues using LangSmith traces.

---

## 🎯 Quick Debugging Workflow

1. **Reproduce the issue** - Generate an email that shows the problem
2. **Find the trace** - Go to LangSmith dashboard → Your project
3. **Analyze the trace** - Click on the trace to see detailed execution
4. **Identify the culprit** - Check which agent is causing issues
5. **Fix and verify** - Update prompts/code, generate again, compare traces

---

## 🔍 Common Issues & How to Debug

### Issue 1: Low Quality Scores (< 7.0)

**Symptom**: Emails consistently score below 7.0

**LangSmith Investigation:**

1. Find a trace with low score
2. Navigate to **EvaluationAgent** step
3. Look at the evaluation breakdown:
   - Which metric is lowest? (clarity, tone, length, spam_risk, personalization)
   - Read the evaluation reasoning in the LLM output

**Solutions by Metric:**

- **Low Clarity Score**: Check `GenerationAgent` → Improve value proposition in prompt
- **Low Tone Score**: Check `PersonaAgent` → Improve tone detection
- **Low Length Score**: Check `GenerationAgent` → Adjust word count targets
- **Low Personalization**: Check `RetrievalAgent` → Improve portfolio matching
- **High Spam Risk**: Check `GenerationAgent` → Remove spam trigger words

### Issue 2: Irrelevant Portfolio Items

**Symptom**: Portfolio items don't match the target role/industry

**LangSmith Investigation:**

1. Find trace with irrelevant portfolio
2. Navigate to **PortfolioAgent** step
3. Check:
   - Input query (role + industry)
   - Vector search results and similarity scores
   - Retrieved portfolio items

**Solutions:**

- **Wrong portfolio items**: Update `data/my_portfolio.csv` with better descriptions
- **Low similarity scores**: Re-index ChromaDB/Pinecone with better embeddings
- **Query mismatch**: Check `PersonaAgent` output → Improve persona extraction

### Issue 3: Generic/Non-Personalized Emails

**Symptom**: Emails feel template-like, lack personalization

**LangSmith Investigation:**

1. Find trace with generic email
2. Check the **full pipeline**:
   - **ScraperAgent**: Did it extract job details correctly?
   - **PersonaAgent**: Did it identify pain points and needs?
   - **GenerationAgent**: Did it use persona insights?

**Solutions:**

- **Scraper failed**: Job URL may be blocked → Add fallback to manual input
- **Weak persona**: Improve `prompts/persona_prompt.txt`
- **Persona not used**: Check `prompts/generation_prompt.txt` → Ensure persona is referenced

### Issue 4: Slow Email Generation (>10 seconds)

**Symptom**: Email generation takes too long

**LangSmith Investigation:**

1. Find a slow trace
2. Look at **Latency** column for each agent
3. Identify the bottleneck agent

**Common Bottlenecks:**

- **ScraperAgent** (5-8s): Job URL scraping is slow
  - Solution: Cache scraped job data
  - Solution: Use faster scraping library
- **PortfolioAgent** (3-5s): Vector search is slow
  - Solution: Reduce portfolio size
  - Solution: Use Pinecone instead of ChromaDB
- **GenerationAgent** (4-6s): LLM generation is slow
  - Solution: Use faster Groq model (llama-3.1-8b-instant)
  - Solution: Reduce prompt length

### Issue 5: Optimization Always Triggered

**Symptom**: Every email goes through OptimizationAgent (score < 7.0)

**LangSmith Investigation:**

1. Find multiple traces
2. Check **EvaluationAgent** scores
3. Identify the consistently low metric

**Solutions:**

- **Always low on one metric**: Focus improvement on that metric
- **Multiple low metrics**: Improve base generation prompt
- **Evaluation too strict**: Adjust evaluation thresholds (not recommended)

### Issue 6: Missing Job Details in Email

**Symptom**: Email doesn't reference specific job requirements

**LangSmith Investigation:**

1. Find trace with missing details
2. Navigate to **ScraperAgent** step
3. Check:
   - Did scraper extract data? (Check `scraped_job_data` field)
   - Was data passed to `GenerationAgent`?

**Solutions:**

- **Scraper failed**: Job site may block scraping → Improve scraper with headers/delays
- **Data not used**: Check `prompts/generation_prompt.txt` → Ensure job data is used
- **Parsing error**: Improve `ScraperAgent` HTML parsing logic

### Issue 7: Wrong Template Selected

**Symptom**: Email style doesn't match target industry

**LangSmith Investigation:**

1. Find trace with wrong template
2. Navigate to **RetrievalAgent** step
3. Check:
   - What was the search query? (role + industry)
   - What templates were retrieved?
   - What were their similarity scores?

**Solutions:**

- **Query mismatch**: Improve persona → role/industry extraction
- **No good templates**: Add more templates in `data/email_templates.json`
- **Template metadata wrong**: Update template `industry` and `title` fields

---

## 📊 Analyzing Trace Patterns

### Healthy Trace Pattern

```
PlannerAgent (0.5s) ✅
  → ScraperAgent (6.2s) ✅
    → PersonaAgent (2.1s) ✅
      → RetrievalAgent (1.8s) ✅
        → PortfolioAgent (2.3s) ✅
          → GenerationAgent (4.5s) ✅
            → EvaluationAgent (2.0s) ✅
              → Score: 8.2 ✅ (No optimization)
```

**Total: ~19 seconds**

### Unhealthy Trace Pattern

```
PlannerAgent (0.5s) ✅
  → ScraperAgent (12.5s) ⚠️ (Too slow)
    → PersonaAgent (2.1s) ✅
      → RetrievalAgent (1.8s) ✅
        → PortfolioAgent (2.3s) ✅
          → GenerationAgent (4.5s) ✅
            → EvaluationAgent (2.0s) ✅
              → Score: 6.3 ⚠️ (Triggers optimization)
                → OptimizationAgent (5.2s) ⚠️
```

**Total: ~31 seconds** (Too slow!)

---

## 🔧 Advanced Debugging Techniques

### 1. Compare Good vs. Bad Traces

Find two traces:

- One with high score (8.5+)
- One with low score (<7.0)

Compare side-by-side:

- Persona extraction differences
- Template selection differences
- Portfolio matching differences
- LLM output differences

### 2. Track Changes Over Time

After making improvements:

1. Generate 10 test emails
2. Note average score and latency
3. Make your change
4. Generate 10 more test emails
5. Compare metrics in LangSmith

### 3. Filter by Error

In LangSmith dashboard:

- Filter: `status = "error"`
- Find traces that failed completely
- Check error messages in last agent step

### 4. Search by Metadata

Add custom tags to trace specific scenarios:

```python
from langsmith import traceable

@traceable(
    tags=["test-case-1", "low-score"],
    metadata={"test_id": "debugging-session-1"}
)
def generate_test_email():
    # Your test code
    pass
```

Then filter in LangSmith: `tags = "low-score"`

---

## 💡 Pro Tips

### 1. **Create a Debug Endpoint**

Add to `main.py`:

```python
@app.post("/debug-generate")
async def debug_generate(request: EmailRequest):
    """Generate with extra debug logging"""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    # ... rest of generate logic
    # Returns email + full trace URL
```

### 2. **Test Individual Agents**

Test agents in isolation:

```python
from agents.persona_agent import PersonaAgent

agent = PersonaAgent()
result = agent.analyze({
    "role": "ML Engineer",
    "industry": "FinTech"
})
print(result)
```

Check LangSmith for just the PersonaAgent trace.

### 3. **Use Trace Annotations**

Add comments to traces:

```python
from langsmith import Client

client = Client()
run = client.read_run(run_id="...")
client.create_feedback(
    run_id=run.id,
    key="user-review",
    score=1.0,
    comment="Perfect email, used as template"
)
```

### 4. **Monitor Production**

Set up alerts in LangSmith:

- Average latency > 20 seconds
- Error rate > 5%
- Low average score < 7.5

---

## 📖 LangSmith Trace Reading Guide

### Understanding Trace Structure

```
📦 PlannerAgent [Root]
  ├─ 📄 Input: {role, industry, job_url}
  ├─ ⚙️ LLM Call: Groq llama-3.1-8b-instant
  │   ├─ Prompt: "You are a planner agent..."
  │   ├─ Tokens: 1,245 (input) + 342 (output)
  │   ├─ Latency: 0.52s
  │   └─ Cost: $0.0023
  ├─ 🔗 Child: ScraperAgent
  └─ 📄 Output: {scraped_data, persona, email, score}
```

**Key Fields:**

- **Input**: What data went into the agent
- **LLM Call**: The actual Groq API call
  - **Prompt**: Full prompt sent to LLM (check for correctness)
  - **Tokens**: Monitor token usage for cost optimization
  - **Latency**: Identify slow calls
- **Output**: What the agent returned
- **Child Runs**: Sub-agents or tool calls

---

## 🚀 Performance Optimization Checklist

Using LangSmith traces, optimize:

- [ ] **Reduce Latency**
  - [ ] Identify slowest agent (>5s)
  - [ ] Optimize prompts (shorter = faster)
  - [ ] Cache frequently used results
  - [ ] Use faster models where possible

- [ ] **Reduce Token Usage**
  - [ ] Shorten prompts
  - [ ] Remove unnecessary context
  - [ ] Use smaller models for simple tasks

- [ ] **Improve Quality**
  - [ ] Analyze low-score traces
  - [ ] Improve prompts based on failure patterns
  - [ ] Add more relevant templates/portfolio items

- [ ] **Reduce Errors**
  - [ ] Find error traces
  - [ ] Add error handling for common failures
  - [ ] Add input validation

---

## 🎓 Learn More

- [LangSmith Debugging Guide](https://docs.smith.langchain.com/evaluation/how_to_guides/debug)
- [LangChain Tracing](https://python.langchain.com/docs/langsmith/tracing)
- [Prompt Engineering Best Practices](https://www.promptingguide.ai/)

---

**Happy Debugging! 🐛→✅**
