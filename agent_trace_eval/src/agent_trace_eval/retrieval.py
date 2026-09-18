"""Keyword retrieval over FastPay ops runbooks (no vector DB, CI-safe)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"


class RunbookIndex:
    def __init__(self, docs: list[dict[str, Any]] | None = None) -> None:
        self.docs = docs if docs is not None else json.loads((DATA_DIR / "runbooks.json").read_text())

    def search(self, query: str, top_k: int = 3) -> dict[str, Any]:
        tokens = [t for t in re.split(r"[^a-z0-9_]+", query.lower()) if t]
        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in self.docs:
            hay = " ".join(
                [*doc.get("reason_codes", []), doc.get("title", ""), doc.get("body", "")]
            ).lower()
            score = 0.0
            for code in doc.get("reason_codes", []):
                if code.lower() in query.lower():
                    score += 5.0
            score += sum(1.0 for t in tokens if t in hay)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        hits = scored[:top_k]
        documents = [
            {
                "id": doc["id"],
                "score": round(score, 3),
                "content": json.dumps(
                    {
                        "title": doc["title"],
                        "body": doc["body"],
                        "rules": doc["rules"],
                        "default_action": doc["default_action"],
                        "reason_codes": doc["reason_codes"],
                    }
                ),
            }
            for score, doc in hits
        ]
        return {
            "query": query,
            "data_source": "fastpay-runbooks",
            "documents": documents,
            "count": len(documents),
        }

    def match_action(self, payment: dict[str, Any], runbook_result: dict[str, Any]) -> str | None:
        for doc_wrap in runbook_result.get("documents") or []:
            payload = json.loads(doc_wrap["content"])
            for rule in payload.get("rules") or []:
                when = rule.get("when") or {}
                if all(payment.get(k) == v for k, v in when.items()):
                    return rule["action"]
            if payload.get("default_action"):
                return payload["default_action"]
        return None
