# 🔬 Autonomous Research Agent

Type a topic. Get a structured literature review with citations in under 2 minutes.

![Agent UI](RASS1.png)

An AI agent that autonomously researches any academic topic — searching arXiv & Semantic Scholar, reading abstracts, and producing a structured literature review with citations. Built on the **ReAct** pattern using the raw Anthropic SDK. No LangChain, no frameworks.

## ✨ Features

- **4 real tools**: arXiv search, Semantic Scholar (with citation counts), paper detail fetcher, web scraper
- **ReAct agent loop**: Claude reasons → picks a tool → observes → reasons again
- **Streamlit UI** with live step-by-step progress
- **CLI mode** for terminal use / scripting
- Downloadable Markdown report

## 📸 See it in action

![Entering a topic](RASS2.png)
*Enter any research topic in the UI*

![Agent reasoning live](RASS3.png)
*Claude reasons and selects tools in real time*

![Tool calls happening](RASS4.png)
*Live searches across arXiv and Semantic Scholar*

![Final literature review](rass5.png)
*Structured review with citations, ready to download*

## 🧠 How it works

The agent loop in `agent/core.py` is pure ReAct — no frameworks, no abstractions: