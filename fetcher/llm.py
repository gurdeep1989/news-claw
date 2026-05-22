import json
import ollama

MODEL = "llama3.2:3b"

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
        resp = ollama.generate(
            model=MODEL,
            prompt=PROMPT.format(title=title or "", summary=(rss_summary or "")[:2000]),
        )
        text = resp["response"].strip()
        # Extract JSON object robustly in case model adds extra prose
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]
        data = json.loads(text)
        return {
            "summary": str(data.get("summary", ""))[:500],
            "tags": [str(t).lower() for t in (data.get("tags") or [])][:4],
        }
    except Exception as e:
        return {"summary": "", "tags": [], "error": str(e)}
