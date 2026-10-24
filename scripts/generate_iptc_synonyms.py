"""Generate conservative English search synonyms for IPTC Media Topics.

Uses a local Ollama model. The input vocabulary is preserved; only a
``synonyms`` array is added to each concept.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path


INPUT_PATH = Path(r"C:\Users\yeech\.codex\attachments\c8a40897-bcf3-49c4-b140-e824a1143daf\Pasted text.txt")
OUTPUT_PATH = Path("data/iptc_media_topics_with_synonyms.json")
CHECKPOINT_PATH = Path("data/iptc_synonyms_checkpoint.json")
MODEL = "gemma3:4b"
BATCH_SIZE = 12


def ask_ollama(batch: list[dict[str, str]]) -> dict[str, list[str]]:
    concept_ids = [item["id"] for item in batch]
    prompt = (
        "For each IPTC news topic below, provide up to 4 concise English search synonyms. "
        "Return ONLY a JSON object mapping every supplied id to an array of strings. "
        "Use conservative lexical equivalents, established acronyms, and commonly used "
        "alternate names that mean the same topic in this context. Do not include the "
        "label itself, translations, examples, related topics, broader/narrower topics, "
        "or speculative phrases. Use [] when no clear synonym exists. Keep phrases short.\n\n"
        "Topics:\n" + json.dumps(batch, ensure_ascii=False)
    )
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You create precise, conservative English aliases for a news taxonomy. Output valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "format": {
                "type": "object",
                "properties": {
                    concept_id: {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                    for concept_id in concept_ids
                },
                "required": concept_ids,
                "additionalProperties": False,
            },
            "stream": False,
            "keep_alive": "10m",
            "options": {"temperature": 0.1, "num_ctx": 4096},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["message"]["content"]
    result = json.loads(content)
    if not isinstance(result, dict):
        raise ValueError("Model response must be a JSON object")
    return result


def main() -> None:
    source = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    if CHECKPOINT_PATH.exists():
        aliases = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    else:
        aliases = {}

    concepts = []
    for concept_id, concept in source.items():
        parent_id = concept.get("parent")
        parent = source.get(parent_id, {}) if parent_id else {}
        grandparent_id = parent.get("parent")
        grandparent = source.get(grandparent_id, {}) if grandparent_id else {}
        concepts.append(
            {
                "id": concept_id,
                "label": concept.get("label", ""),
                "definition": concept.get("definition", ""),
                "parent": parent.get("label"),
                "grandparent": grandparent.get("label"),
            }
        )

    pending = [c for c in concepts if c["id"] not in aliases]
    total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE
    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start : start + BATCH_SIZE]
        expected = {c["id"] for c in batch}
        last_error = None
        for attempt in range(3):
            try:
                result = ask_ollama(batch)
                # Some local models wrap the requested map in a top-level key.
                if len(result) == 1 and isinstance(next(iter(result.values())), dict):
                    result = next(iter(result.values()))
                missing = expected - set(result)
                if missing:
                    raise ValueError(
                        f"Missing concept ids: {sorted(missing)}; returned keys: {list(result)[:12]}"
                    )
                for concept_id in expected:
                    values = result[concept_id]
                    if not isinstance(values, list):
                        raise ValueError(f"Synonyms for {concept_id} are not an array")
                    clean = []
                    for value in values:
                        if isinstance(value, str):
                            value = " ".join(value.strip().split())
                            if value and value.casefold() not in {
                                source[concept_id].get("label", "").casefold(),
                                *(s.casefold() for s in clean),
                            }:
                                clean.append(value)
                        if len(clean) == 4:
                            break
                    aliases[concept_id] = clean
                last_error = None
                break
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
                last_error = exc
                time.sleep(2 * (attempt + 1))
        if last_error is not None:
            CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
            CHECKPOINT_PATH.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")
            raise RuntimeError(f"Batch {start // BATCH_SIZE + 1} failed: {last_error}") from last_error

        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHECKPOINT_PATH.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Completed batch {start // BATCH_SIZE + 1}/{total_batches} ({len(aliases)}/{len(source)})", flush=True)

    for concept_id, concept in source.items():
        concept["synonyms"] = aliases.get(concept_id, [])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(source)} concepts to {OUTPUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
