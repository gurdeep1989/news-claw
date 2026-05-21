import json
import os
import time
from google import genai

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client

PROMPT = """You are a news summarizer.

Given the title and raw RSS summary of a news article, return a JSON object with:
- "summary": one tight sentence (max 30 words) capturing what the article says.
- "tags": array of 1–4 lowercase topic tags from this fixed set:
  [politics, business, tech, science, health, sports, entertainment,
   world, crime, weather, opinion, other]

Return ONLY the JSON object, no prose, no markdown fences.

Title: {title}
Summary: {summary}
"""

def summarize(title: str, rss_summary: str) -> dict:
    """Returns {'summary': str, 'tags': list[str]}. Falls back gracefully on errors."""
    try:
        time.sleep(4)
        resp = _get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents=PROMPT.format(title=title or "", summary=(rss_summary or "")[:2000]),
        )
        text = resp.text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        return {
            "summary": str(data.get("summary", ""))[:500],
            "tags": [str(t).lower() for t in (data.get("tags") or [])][:4],
        }
    except Exception as e:
        return {"summary": "", "tags": [], "error": str(e)}
