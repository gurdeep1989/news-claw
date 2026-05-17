import json
import os
import google.generativeai as genai

_model = None

def _get_model():
    global _model
    if _model is None:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        _model = genai.GenerativeModel("gemini-2.0-flash")
    return _model

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
        resp = _get_model().generate_content(
            PROMPT.format(title=title or "", summary=(rss_summary or "")[:2000])
        )
        text = resp.text.strip()
        # Strip accidental code fences
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