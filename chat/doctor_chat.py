import requests
import json
import re
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL


def _extract_message_content(data: dict) -> str:
    """
    OpenRouter normalizes to Chat Completions, but providers can sometimes return
    message.content as a string or as a list of content parts.
    """
    try:
        choice0 = (data.get("choices") or [{}])[0] or {}
        # Some providers include `text` at the choice level.
        if isinstance(choice0.get("text"), str) and choice0.get("text").strip():
            return choice0["text"]

        msg = choice0.get("message") or {}
        # Some providers include `refusal` when they won't answer.
        if isinstance(msg.get("refusal"), str) and msg.get("refusal").strip():
            return msg["refusal"]

        content = msg.get("content", "")
        # Some providers place text in `reasoning` while leaving `content` null.
        if (content is None or content == "") and isinstance(msg.get("reasoning"), str) and msg.get("reasoning").strip():
            return msg["reasoning"]
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for p in content:
                if isinstance(p, str):
                    parts.append(p)
                elif isinstance(p, dict):
                    if isinstance(p.get("text"), str):
                        parts.append(p["text"])
                    elif isinstance(p.get("content"), str):
                        parts.append(p["content"])
                    elif isinstance(p.get("value"), str):
                        parts.append(p["value"])
                    elif isinstance(p.get("output_text"), str):
                        parts.append(p["output_text"])
            return "\n".join([x for x in parts if x]).strip()
        if content is not None:
            return str(content)

        # Last resort: surface error message if present
        err = data.get("error")
        if isinstance(err, dict) and isinstance(err.get("message"), str):
            return err["message"]
        return ""
    except Exception:
        return ""


def _sanitize_plain_text(text: str) -> str:
    if not text:
        return ""

    t = text.strip()
    raw_original = t

    # Remove common markdown artifacts: headings, bold markers, code fences, bullets
    t = re.sub(r"^#{1,6}\s+", "", t, flags=re.MULTILINE)
    t = t.replace("**", "").replace("__", "")
    # Keep code-fence contents; remove only the fence markers.
    t = re.sub(r"```(?:\w+)?\s*\n?", "", t)
    t = t.replace("```", "")
    t = t.replace("`", "")
    t = re.sub(r"^\s*[-*•]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"^\s*\d+\.\s+", "", t, flags=re.MULTILINE)

    # Normalize spacing
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = t.strip()

    # Remove common "thinking out loud" lead-ins if a provider returns reasoning text.
    sentences = re.split(r"(?<=[.!?])\s+", t)
    drop_prefixes = (
        "okay,", "ok,", "the user", "let me", "i need", "i should", "first,", "second,", "now,",
    )
    cleaned_sentences = []
    for s in sentences:
        ss = s.strip()
        if not ss:
            continue
        low = ss.lower()
        if low.startswith(drop_prefixes):
            continue
        if "markdown" in low or "bullet" in low or "lists" in low:
            continue
        if "i need" in low or "i should" in low:
            continue
        cleaned_sentences.append(ss)
    t = " ".join(cleaned_sentences).strip() or t

    # If sanitization accidentally removed everything, fall back to a lighter cleanup.
    if not t:
        fallback = raw_original.replace("**", "").replace("__", "").strip()
        fallback = re.sub(r"^#{1,6}\s+", "", fallback, flags=re.MULTILINE).strip()
        return fallback[:1200].strip()

    return t


def _truncate_sentences(text: str, max_sentences: int = 5) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    # Split on sentence-ending punctuation while keeping simple behavior.
    parts = re.split(r"(?<=[.!?])\s+", t)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= max_sentences:
        return t
    return " ".join(parts[:max_sentences]).strip()

def get_reply(report_type: str, extracted_values: dict, prediction_result: dict, conversation_history: list) -> str:
    values_str = json.dumps(extracted_values, indent=2)
    result_str = json.dumps(prediction_result, indent=2)
    
    system_prompt = f"""You are MedAI Doctor, a calm medical assistant.

Context: The patient is asking about their {report_type.upper()} lab report.
Extracted values (JSON):
{values_str}

AI prediction result (JSON):
{result_str}

Response rules (critical):
- Output MUST be plain text only (no markdown, no headings, no bullet lists, no bold/asterisks).
- Be concise by default: 2 to 5 short sentences.
- Explain simply and reassuringly. Mention only the most relevant findings unless asked.
- If something is potentially abnormal, say it gently and suggest discussing with a clinician.
- Include a brief reminder that this is not a diagnosis (one short sentence, not repeated)."""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENROUTER_MODEL,
                "max_tokens": 220,
                "temperature": 0.3,
                "messages": [{"role": "system", "content": system_prompt}] + conversation_history,
            }
        )
        response.raise_for_status()
        raw = _extract_message_content(response.json())
        cleaned = _truncate_sentences(_sanitize_plain_text(raw), 5)
        return cleaned or "Sorry — I couldn’t generate a response right now. Please try again."
    except Exception as e:
        return f"Error connecting to Doctor Chat: {e}"


def get_assistant_reply(message: str, conversation_history: list) -> str:
    system_prompt = """You are MedAI Assistant, a calm and professional medical information assistant.

Response rules (critical):
- Output MUST be plain text only (no markdown, no headings, no bullet lists, no bold/asterisks).
- Be concise by default: 2 to 5 short sentences.
- Explain simply, avoid jargon unless the user asks.
- If asked for diagnosis or treatment, recommend discussing with a licensed clinician.
- Include a brief reminder that this is not a diagnosis (one short sentence, not repeated)."""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENROUTER_MODEL,
                "max_tokens": 220,
                "temperature": 0.3,
                "messages": [{"role": "system", "content": system_prompt}] + conversation_history + [{"role": "user", "content": message}],
            }
        )
        response.raise_for_status()
        data = response.json()
        raw = _extract_message_content(data)
        try:
            print(f"[assistant_chat] extracted_len={len(raw or '')} extracted_preview={repr((raw or '')[:200])}")
        except Exception:
            pass
        cleaned = _truncate_sentences(_sanitize_plain_text(raw), 5)
        if not cleaned:
            try:
                preview = json.dumps(data, ensure_ascii=False)[:1200]
            except Exception:
                preview = str(data)[:1200]
            print(f"[assistant_chat] empty content preview: {preview}")
        return cleaned or "Sorry — I couldn’t generate a response right now. Please try again."
    except Exception as e:
        return f"Error connecting to Assistant Chat: {e}"
