# 🔍 LangSmith Integration Guide

LangSmith is a powerful platform for debugging, testing, and monitoring LangChain applications. It provides detailed traces of your agent executions, helping you understand and optimize your cold outreach AI system.

## 📋 What You'll Get with LangSmith

- **🔎 Detailed Traces**: See every LLM call, agent decision, and tool usage
- **📊 Performance Metrics**: Track latency, token usage, and costs
- **🐛 Debugging**: Identify bottlenecks and errors in your agent pipeline
- **📈 Analytics**: Monitor usage patterns and quality over time
- **🔄 Comparisons**: Compare different agent runs side-by-side

---

## 🚀 Setup Instructions

### 1. Get Your LangSmith API Key

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign up or log in (free tier available)
3. Navigate to **Settings** → **API Keys**
4. Create a new API key
5. Copy the key

### 2. Configure Environment Variables

Open your `.env` file and replace the placeholder with your actual API key:

```bash
# LangSmith Tracing (Optional - for monitoring and debugging)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_pt_your_actual_api_key_here
LANGCHAIN_PROJECT=cold-outreach-ai-agent
```

**Environment Variables Explained:**

- `LANGCHAIN_TRACING_V2=true` - Enables LangSmith tracing
- `LANGCHAIN_ENDPOINT` - LangSmith API endpoint (use default)
- `LANGCHAIN_API_KEY` - Your personal API key from step 1
- `LANGCHAIN_PROJECT` - Project name in LangSmith (customize if desired)

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `langsmith` package along with other dependencies.

### 4. Restart Your Application

```bash
python main.py
```

You should see this message at startup:

```
✅ LangSmith tracing enabled for project: cold-outreach-ai-agent
```

---

## 📊 Viewing Traces in LangSmith

### Access Your Dashboard

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Select your project: `cold-outreach-ai-agent`
3. View traces in the **Traces** tab

### What You'll See

Each email generation creates a trace showing:

1. **PlannerAgent Execution**
   - Input: role, industry, job URL
   - Orchestration decisions
   - Agent coordination

2. **PersonaAgent Execution**
   - Job posting analysis
   - Persona extraction
   - Pain point identification

3. **ScraperAgent Execution** (if job_url provided)
   - Web scraping results
   - Parsed job details

4. **RetrievalAgent Execution**
   - Portfolio vector search
   - Semantic similarity scores
   - Retrieved projects

5. **GenerationAgent Execution**
   - Email template selection
   - Content generation
   - Personalization

6. **EvaluationAgent Execution**
   - Quality scoring
   - Feedback analysis

7. **OptimizationAgent Execution** (if score < 7)
   - Refinement suggestions
   - Improved email version

### Useful Filters

In the LangSmith dashboard, you can filter traces by:

- **Status**: Success, Error, Pending
- **Duration**: Find slow operations
- **Tags**: Custom metadata (you can add these)
- **Feedback**: Add manual ratings

---

## 🎯 Advanced Usage

### Adding Custom Metadata to Traces

You can add custom tags and metadata to traces for better organization:

```python
from langsmith import traceable

@traceable(
    run_type="chain",
    tags=["email-generation", "lead-sourcing"],
    metadata={"customer": "acme-corp"}
)
def my_custom_function():
    # Your code here
    pass
```

### Filtering Specific Agents

To trace only specific agents, modify individual agent files:

```python
# In agents/planner_agent.py
from langsmith import traceable

class PlannerAgent:
    @traceable(name="PlannerAgent_Execute", run_type="chain")
    def execute(self, request):
        # Agent logic
        pass
```

### Disabling Tracing Temporarily

Set `LANGCHAIN_TRACING_V2=false` in your `.env` file or comment it out:

```bash
# LANGCHAIN_TRACING_V2=true  # Disabled
```

### Using Different Projects for Dev/Prod

Update the project name based on environment:

```bash
# Development
LANGCHAIN_PROJECT=cold-outreach-dev

# Production
LANGCHAIN_PROJECT=cold-outreach-prod
```

---

## 📈 Monitoring Best Practices

### 1. **Track Key Metrics**

- Average email generation time
- Token usage per request
- Error rates by agent
- Quality score distribution

### 2. **Set Up Alerts**

- High latency (>10 seconds)
- Error spikes
- Cost thresholds

### 3. **Regular Reviews**

- Weekly trace analysis
- Identify optimization opportunities
- Monitor prompt effectiveness

### 4. **A/B Testing**

- Test different prompts
- Compare agent strategies
- Measure quality improvements

---

## 🐛 Debugging with LangSmith

### Common Issues

**Issue**: Traces not appearing in LangSmith

- **Solution**: Verify `LANGCHAIN_API_KEY` is correct
- **Solution**: Check internet connectivity
- **Solution**: Ensure `LANGCHAIN_TRACING_V2=true`

**Issue**: Slow email generation

- **Solution**: Check LangSmith traces to identify bottleneck agents
- **Solution**: Look for high-latency LLM calls
- **Solution**: Optimize prompts in `/prompts` directory

**Issue**: Low quality scores

- **Solution**: Review evaluation traces
- **Solution**: Check portfolio retrieval relevance
- **Solution**: Examine persona extraction accuracy

---

## 💰 Cost Tracking

LangSmith automatically tracks:

- **Token usage** per request
- **Cost estimates** based on model pricing
- **Usage trends** over time

Navigate to **Settings** → **Usage** to see your consumption.

---

## 🔒 Security Notes

- **Keep your API key private** - Never commit it to version control
- **.env file is gitignored** - Safe to store locally
- **Production deployments** - Use environment variable injection
- **Heroku/Render** - Add `LANGCHAIN_API_KEY` as a config var
- **Docker** - Pass via `-e` flag or docker-compose

---

## 📚 Additional Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangChain Tracing Guide](https://python.langchain.com/docs/langsmith/tracing)
- [LangSmith Cookbook](https://github.com/langchain-ai/langsmith-cookbook)
- [Discord Community](https://discord.gg/langchain)

---

## ✅ Quick Verification

After setup, verify LangSmith is working:

1. Start your server: `python main.py`
2. Send a test request: `POST /generate`
3. Check LangSmith dashboard for new traces
4. Look for your project: `cold-outreach-ai-agent`

You should see a trace with all 6-7 agents in the execution path.

---

## 🎉 You're All Set!

LangSmith is now tracking your cold outreach AI agent. Start generating emails and explore the traces to understand your system better!

**Questions?** Check the [documentation](https://docs.smith.langchain.com/) or reach out to the LangChain community.
