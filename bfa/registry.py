from rank_bm25 import BM25Okapi
import numpy as np
import re
import unicodedata

AGENT_REGISTRY = {}
BM25_INDEX = None
BM25_KEYS = []

BOOST_TOOL = 0.05


def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    return text


def tokenize(text: str):
    text = normalize(text)
    return re.findall(r"\w+", text)


def build_index():
    global BM25_INDEX, BM25_KEYS
    corpus = []
    keys = []
    for skill_id, data in AGENT_REGISTRY.items():
        text = data.get("search_text") or ". ".join([
            data.get("name", ""),
            data.get("description", ""),
            ". ".join(data.get("tags", [])),
        ])
        tokens = tokenize(text)
        if not tokens:
            continue
        corpus.append(tokens)
        keys.append(skill_id)
    if corpus:
        BM25_INDEX = BM25Okapi(corpus)
        BM25_KEYS = keys


def search_bm25(query: str, top_k: int = 3, filter_type: str | None = None):
    if not BM25_INDEX:
        return []

    tokens = tokenize(query)
    if not tokens:
        return []

    scores = BM25_INDEX.get_scores(tokens)
    max_score = max(scores) if len(scores) > 0 else 1
    if max_score == 0:
        max_score = 1

    ranked_idx = np.argsort(scores)[::-1]
    results = []

    for idx in ranked_idx:
        skill_id = BM25_KEYS[idx]
        data = AGENT_REGISTRY[skill_id]

        if filter_type and data.get("type") != filter_type:
            continue

        raw_score = float(scores[idx])
        norm_score = raw_score / max_score

        if not filter_type and data.get("type") == "tool":
            norm_score += BOOST_TOOL

        results.append({
            "skill": skill_id,
            "score": raw_score,
            "normalized_score": norm_score,
            "type": data.get("type", "agent"),
            "data": data,
        })

        if len(results) >= top_k:
            break

    return results


def resolve_agent(query: str, top_k: int = 3, threshold: float = 0.3, filter_type: str | None = None):
    results = search_bm25(query, top_k=top_k, filter_type=filter_type)
    if not results:
        return None

    best = results[0]

    if best["normalized_score"] < threshold:
        return {"type": "no_confident_match", "best": None, "candidates": results}

    return {"type": "bm25", "best": best, "candidates": results}