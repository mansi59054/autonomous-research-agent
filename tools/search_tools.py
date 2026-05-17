"""
Search tools for the Research Agent.
Each function is also exposed as a tool schema for Claude to call.
"""

import re
import time
import requests
from bs4 import BeautifulSoup


# ── Tool schemas (passed to Claude) ──────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "search_arxiv",
        "description": (
            "Search arXiv for academic papers. Returns titles, authors, abstracts, "
            "arXiv IDs, and PDF links. Use this first when exploring a research topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g. 'quantum reservoir computing energy forecasting'",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of papers to return (default 8, max 20)",
                    "default": 8,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_semantic_scholar",
        "description": (
            "Search Semantic Scholar for papers with citation counts and influence scores. "
            "Great for finding highly-cited foundational work on a topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of papers to return (default 8, max 20)",
                    "default": 8,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_paper_details",
        "description": (
            "Fetch full details for a specific arXiv paper by its ID (e.g. '2301.07234'). "
            "Returns the full abstract, authors, categories, and submission date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "arxiv_id": {
                    "type": "string",
                    "description": "arXiv paper ID like '2301.07234' (without 'arXiv:' prefix)",
                },
            },
            "required": ["arxiv_id"],
        },
    },
    {
        "name": "scrape_webpage",
        "description": (
            "Scrape and extract the main text content from a webpage URL. "
            "Use for reading blog posts, project pages, or non-arXiv sources."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL to scrape, e.g. 'https://example.com/paper'",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Max characters to return (default 4000)",
                    "default": 4000,
                },
            },
            "required": ["url"],
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

def search_arxiv(query: str, max_results: int = 8) -> dict:
    """Search arXiv using the public API."""
    max_results = min(max_results, 20)
    time.sleep(1)
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        resp = requests.get(base_url, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"arXiv request failed: {e}"}

    soup = BeautifulSoup(resp.text, "lxml-xml")
    entries = soup.find_all("entry")

    papers = []
    for entry in entries:
        arxiv_id_raw = entry.find("id").text.strip()
        arxiv_id = arxiv_id_raw.split("/abs/")[-1]

        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": entry.find("title").text.strip().replace("\n", " "),
                "authors": [a.find("name").text for a in entry.find_all("author")][:5],
                "abstract": entry.find("summary").text.strip().replace("\n", " ")[:600],
                "published": entry.find("published").text[:10],
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
                "categories": [c.get("term") for c in entry.find_all("category")],
            }
        )

    return {"source": "arXiv", "query": query, "count": len(papers), "papers": papers}


def search_semantic_scholar(query: str, max_results: int = 8) -> dict:
    """Search Semantic Scholar public API (no key required)."""
    max_results = min(max_results, 20)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,year,citationCount,influentialCitationCount,abstract,externalIds,url",
    }

    try:
        time.sleep(0.5)  # be polite
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {"error": f"Semantic Scholar request failed: {e}"}

    papers = []
    for p in data.get("data", []):
        arxiv_id = (p.get("externalIds") or {}).get("ArXiv", "")
        papers.append(
            {
                "title": p.get("title", ""),
                "authors": [a["name"] for a in (p.get("authors") or [])[:5]],
                "year": p.get("year"),
                "citation_count": p.get("citationCount", 0),
                "influential_citations": p.get("influentialCitationCount", 0),
                "abstract": (p.get("abstract") or "")[:600],
                "arxiv_id": arxiv_id,
                "url": p.get("url", ""),
            }
        )

    return {
        "source": "Semantic Scholar",
        "query": query,
        "count": len(papers),
        "papers": papers,
    }


def fetch_paper_details(arxiv_id: str) -> dict:
    """Fetch a single paper's full metadata from arXiv."""
    arxiv_id = arxiv_id.strip().lstrip("arXiv:").lstrip("arxiv:")
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch paper: {e}"}

    soup = BeautifulSoup(resp.text, "lxml-xml")
    entry = soup.find("entry")
    if not entry:
        return {"error": f"Paper {arxiv_id} not found on arXiv"}

    return {
        "arxiv_id": arxiv_id,
        "title": entry.find("title").text.strip().replace("\n", " "),
        "authors": [a.find("name").text for a in entry.find_all("author")],
        "abstract": entry.find("summary").text.strip().replace("\n", " "),
        "published": entry.find("published").text[:10],
        "updated": entry.find("updated").text[:10],
        "categories": [c.get("term") for c in entry.find_all("category")],
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
    }


def scrape_webpage(url: str, max_chars: int = 4000) -> dict:
    """Scrape and clean text from a webpage."""
    headers = {"User-Agent": "Mozilla/5.0 (research-agent/1.0; academic use)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch {url}: {e}"}

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return {
        "url": url,
        "content": text[:max_chars],
        "truncated": len(text) > max_chars,
        "total_chars": len(text),
    }


# ── Dispatcher ────────────────────────────────────────────────────────────────

def run_tool(tool_name: str, tool_input: dict) -> dict:
    """Route a tool call from Claude to the correct function."""
    dispatch = {
        "search_arxiv": search_arxiv,
        "search_semantic_scholar": search_semantic_scholar,
        "fetch_paper_details": fetch_paper_details,
        "scrape_webpage": scrape_webpage,
    }
    fn = dispatch.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: {tool_name}"}
    return fn(**tool_input)
