# ✅ LangSmith Integration Verification Checklist

Use this checklist to verify your LangSmith integration is working correctly.

---

## 📋 Pre-Flight Checklist

### Step 1: Dependencies

- [ ] Run `pip install -r requirements.txt`
- [ ] Verify `langsmith` is installed: `pip show langsmith`
- [ ] Should show version `0.1.0` or higher

### Step 2: Environment Variables

- [ ] Open your `.env` file
- [ ] Verify these variables exist:
  ```bash
  LANGCHAIN_TRACING_V2=true
  LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
  LANGCHAIN_API_KEY=lsv2_pt_your_actual_key_here
  LANGCHAIN_PROJECT=cold-outreach-ai-agent
  ```
- [ ] Replace `your_actual_key_here` with real API key from [smith.langchain.com](https://smith.langchain.com)

### Step 3: LangSmith Account

- [ ] Have account at [smith.langchain.com](https://smith.langchain.com) (free tier OK)
- [ ] Can access dashboard
- [ ] Have created an API key (Settings → API Keys)

---

## 🧪 Functional Testing

### Test 1: Server Startup

```bash
python main.py
```

**Expected Output:**

```
✅ LangSmith tracing enabled for project: cold-outreach-ai-agent
🚀 Starting EmailCraft AI...
✅ Server ready - agents will initialize on first request
```

- [ ] See LangSmith confirmation message
- [ ] No errors during startup
- [ ] Server starts on port 8000

### Test 2: Generate Test Email

**Option A: Via Web UI**

1. Open http://localhost:8000
2. Fill in email form:
   - Role: "Machine Learning Engineer"
   - Industry: "FinTech"
   - Your Name: "Test User"
3. Click "Generate Email"
4. Wait for result

**Option B: Via API**

```bash
curl -X POST http://localhost:8000/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"role\":\"ML Engineer\",\"industry\":\"FinTech\",\"sender_name\":\"Test\"}"
```

- [ ] Email generated successfully
- [ ] No errors in console
- [ ] Response includes email body and score

### Test 3: Verify Trace in LangSmith

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Select project: `cold-outreach-ai-agent`
3. Click "Traces" tab
4. Look for most recent trace (should be <1 minute old)

**Expected Trace Structure:**

```
📦 PlannerAgent
  └─ 🔗 PersonaAgent
      └─ 🔗 RetrievalAgent
          └─ 🔗 PortfolioAgent
              └─ 🔗 GenerationAgent
                  └─ 🔗 EvaluationAgent
```

- [ ] Trace appears in dashboard (within 5 seconds)
- [ ] Can click and expand trace
- [ ] See all agents (6-7 depending on optimization)
- [ ] Can view prompts and outputs
- [ ] Latency and token counts visible

---

## 🔍 Detailed Trace Verification

Click on your trace and verify each component:

### PlannerAgent

- [ ] Input shows: `{role, industry, tone, sender_name}`
- [ ] Output shows: `{final_email, final_score, portfolio_items_used}`
- [ ] Has child runs (other agents)

### PersonaAgent

- [ ] Input shows: `{role, industry}`
- [ ] Output shows: `{pain_points, needs, communication_style}`
- [ ] LLM call visible with full prompt

### RetrievalAgent

- [ ] Input shows: `{role, industry}`
- [ ] Output shows: `{templates: [...]}`
- [ ] Vector search performed

### PortfolioAgent

- [ ] Input shows: `{role, industry}`
- [ ] Output shows: `{portfolio_items: [...]}`
- [ ] Vector search performed

### GenerationAgent

- [ ] Input shows: `{persona, templates, portfolio}`
- [ ] Output shows: `{subject_line, body, cta}`
- [ ] LLM call visible

### EvaluationAgent

- [ ] Input shows: `{generated_email}`
- [ ] Output shows: `{final_score, clarity_score, tone_score, ...}`
- [ ] All 5 metric scores visible

---

## 🎯 Feature Testing

### Feature 1: Job URL Scraping

Generate email with job URL:

```json
{
  "job_url": "https://www.linkedin.com/jobs/view/123456",
  "sender_name": "Test"
}
```

- [ ] ScraperAgent appears in trace
- [ ] Scraped data visible in trace
- [ ] Email includes job-specific details

### Feature 2: Lead Generation

Test lead sourcing endpoint:

```json
{
  "business_type": "software companies",
  "location": "San Francisco, CA",
  "max_results": 5
}
```

- [ ] Multiple traces created (one per lead)
- [ ] Each trace tagged with lead info
- [ ] All traces visible in dashboard

### Feature 3: Batch Processing

Upload CSV with 3-5 rows and generate batch emails.

- [ ] Multiple traces created
- [ ] Traces appear over time (30s delay between)
- [ ] Can filter/group traces by batch

---

## 📊 Metrics Verification

In LangSmith dashboard, check:

### Latency

- [ ] Total trace time: 15-30 seconds (normal)
- [ ] No single agent > 10 seconds
- [ ] ScraperAgent is usually slowest (OK)

### Token Usage

- [ ] Input tokens: 1,000-3,000 per trace
- [ ] Output tokens: 300-800 per trace
- [ ] Total tokens: 1,500-4,000 per email

### Cost (if available)

- [ ] Cost per trace: $0.001-0.005 (Groq is cheap)
- [ ] Daily cost tracking visible

### Error Rate

- [ ] No errors in test traces
- [ ] All traces show "success" status

---

## 🐛 Troubleshooting Tests

### Test Error Handling

Intentionally trigger an error:

```json
{
  "role": "",
  "industry": "",
  "sender_name": ""
}
```

- [ ] Error trace appears in LangSmith
- [ ] Error message visible in trace
- [ ] Can identify which agent failed

### Test Slow Performance

Generate email with job URL to LinkedIn (slow scraper):

```json
{
  "job_url": "https://www.linkedin.com/jobs/view/123456",
  "sender_name": "Test"
}
```

- [ ] Trace shows high latency for ScraperAgent
- [ ] Can identify bottleneck
- [ ] Total time visible in trace metadata

---

## 🔒 Security Verification

### API Key Protection

- [ ] `.env` is in `.gitignore`
- [ ] API key not visible in trace outputs
- [ ] API key not logged in console
- [ ] `.env` not committed to git

### Production Readiness

- [ ] Can disable tracing by setting `LANGCHAIN_TRACING_V2=false`
- [ ] Tracing doesn't block requests (asynchronous)
- [ ] No sensitive data in traces (emails are OK, passwords not OK)

---

## 📈 Performance Impact Test

### With Tracing Enabled

```bash
# Set LANGCHAIN_TRACING_V2=true
python main.py
# Generate 5 test emails, measure time
```

- [ ] Measure average generation time: **\_\_\_** seconds

### With Tracing Disabled

```bash
# Set LANGCHAIN_TRACING_V2=false
python main.py
# Generate 5 test emails, measure time
```

- [ ] Measure average generation time: **\_\_\_** seconds

**Expected Impact:** <100ms difference (negligible)

---

## ✅ Sign-Off

### Final Verification

- [ ] All tests passed
- [ ] Traces visible in dashboard
- [ ] No errors in production
- [ ] Team members can access dashboard (if team project)
- [ ] Documentation reviewed

### Optional: Advanced Features

- [ ] Set up alerts for errors
- [ ] Create custom dashboards
- [ ] Add trace annotations
- [ ] Set up A/B testing

---

## 🎉 Verification Complete!

If all checkboxes are checked, your LangSmith integration is working perfectly!

**Next Steps:**

1. Generate production emails and monitor traces
2. Set up alerts for anomalies
3. Use traces to optimize prompts
4. Share dashboard with team

---

## 📝 Notes

Use this section for any observations or issues found during testing:

```
Date: _______________
Tester: _______________

Observations:
-
-
-

Issues Found:
-
-

Resolved:
-
-
```

---

**Happy Tracing! 🎯**
