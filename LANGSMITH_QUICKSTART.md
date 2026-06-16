# 🚀 LangSmith Quick Start (5 Minutes)

Get LangSmith tracing up and running in 5 minutes.

---

## Step 1: Get API Key (2 minutes)

1. Go to **[smith.langchain.com](https://smith.langchain.com)**
2. Sign up (free) or log in
3. Click **Settings** → **API Keys**
4. Click **Create API Key**
5. Copy the key (starts with `lsv2_pt_...`)

---

## Step 2: Update .env (1 minute)

Open `.env` file and add/update:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_paste_your_key_here
LANGCHAIN_PROJECT=cold-outreach-ai-agent
```

Save the file.

---

## Step 3: Install & Run (2 minutes)

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python main.py
```

Look for this message:

```
✅ LangSmith tracing enabled for project: cold-outreach-ai-agent
```

---

## Step 4: Test It

### Generate a Test Email

Open browser → http://localhost:8000

Fill in:

- **Role**: Machine Learning Engineer
- **Industry**: FinTech
- **Your Name**: Test User

Click **Generate Email**

### View the Trace

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Select project: **cold-outreach-ai-agent**
3. Click **Traces** tab
4. See your trace! Click it to explore.

---

## What You'll See

```
📦 PlannerAgent (0.5s)
  └─ 🔗 PersonaAgent (2.1s)
      └─ 🔗 RetrievalAgent (1.8s)
          └─ 🔗 PortfolioAgent (2.3s)
              └─ 🔗 GenerationAgent (4.5s)
                  └─ 🔗 EvaluationAgent (2.0s)
```

Click each agent to see:

- ✅ Input/Output
- 📝 Full prompts
- 🪙 Token counts
- ⏱️ Latency
- 💰 Cost estimates

---

## Done! 🎉

You now have full tracing and monitoring for your AI agent.

### What's Next?

- 📖 Read [LANGSMITH_SETUP.md](LANGSMITH_SETUP.md) for detailed features
- 🐛 Read [DEBUGGING_WITH_LANGSMITH.md](DEBUGGING_WITH_LANGSMITH.md) for debugging tips
- ✅ Use [LANGSMITH_VERIFICATION_CHECKLIST.md](LANGSMITH_VERIFICATION_CHECKLIST.md) to verify everything

---

## Turn Off Tracing

To disable (for local dev):

```bash
# In .env
LANGCHAIN_TRACING_V2=false
```

---

## Troubleshooting

**Traces not appearing?**

- Check API key is correct
- Verify `LANGCHAIN_TRACING_V2=true`
- Wait 5-10 seconds for trace to upload

**Server won't start?**

- Run `pip install langsmith`
- Check for syntax errors in `.env`

**Need help?**

- [LangSmith Docs](https://docs.smith.langchain.com/)
- [Discord Community](https://discord.gg/langchain)

---

**That's it! Simple, right?** 🚀
