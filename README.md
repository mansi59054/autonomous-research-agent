# 🔬 Autonomous Research Agent

An AI agent that autonomously researches any academic topic — searching arXiv & Semantic Scholar, reading abstracts, and producing a structured literature review with citations. Built on the **ReAct** pattern using the Anthropic SDK.

## ✨ Features

- **4 real tools**: arXiv search, Semantic Scholar (with citation counts), paper detail fetcher, web scraper
- **ReAct agent loop**: Claude reasons → picks a tool → observes → reasons again
- **Streamlit UI** with live step-by-step progress
- **CLI mode** for terminal use / scripting
- Downloadable Markdown report

## 🚀 Setup (5 minutes)

### 1. Clone / unzip the project

```bash
cd research-agent
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
# Open .env and paste your Anthropic API key
# Get one at: https://console.anthropic.com/
```

### 5. Run it

**Streamlit UI (recommended):**
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

**CLI:**
```bash
python run_cli.py "quantum reservoir computing"
python run_cli.py "spiking neural networks" --output review.md
```

## 🗂️ Project structure

```
research-agent/
├── app.py              ← Streamlit UI
├── run_cli.py          ← CLI runner
├── requirements.txt
├── .env.example        ← Copy to .env and add your key
├── agent/
│   ├── core.py         ← ReAct agent loop (the brain)
│   └── prompts.py      ← System + user prompts
└── tools/
    └── search_tools.py ← 4 tools: arXiv, Semantic Scholar, fetcher, scraper
```

## 🧠 How it works

The agent loop in `agent/core.py` is pure **ReAct**:

```
User topic
   ↓
Claude reasons about what to search
   ↓
Claude calls a tool (e.g. search_arxiv)
   ↓
Tool result added to context
   ↓
Claude reasons again — refine, fetch details, or conclude
   ↓
... repeats up to max_iterations ...
   ↓
Claude writes the final structured report
```

No LangChain, no frameworks — just raw Anthropic SDK calls with tool use.

## 💡 Example topics to try

- `quantum reservoir computing`
- `spiking neural networks for edge AI`
- `diffusion models for protein structure prediction`
- `neuromorphic computing energy efficiency`
- `transformers for time series forecasting`

## 📋 Requirements

- Python 3.9+
- Anthropic API key (claude-sonnet-4 recommended for best results)
- Internet access (arXiv and Semantic Scholar APIs are free, no key needed)
