"""Production progress and safe presentation helpers, independent of Streamlit."""
from datetime import datetime, timezone
import re

STAGES = [
    ("assets", "Fichiers source"), ("story", "Histoire"),
    ("illustrations", "Illustrations"), ("pdf", "Assemblage PDF"),
    ("upload", "Enregistrement"), ("complete", "Livre prêt"),
]


def safe_error(error):
    text = str(error)
    text = re.sub(r"(?:sk-|sb_secret_)[A-Za-z0-9_\-]+", "[clé masquée]", text)
    text = re.sub(r"(?i)Bearer\s+\S+", "Bearer [masqué]", text)
    text = re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[jeton masqué]", text)
    return text[:1200]


def progress_percent(stage, book_index=1, book_total=1, page_index=0, page_total=10):
    fraction = {"assets": .02, "story": .08, "pdf": .88, "upload": .96, "complete": 1}.get(stage, 0)
    if stage == "illustrations":
        fraction = .12 + .70 * min(max(page_index / max(page_total, 1), 0), 1)
    if stage == "complete":
        return 100
    return min(99, max(0, round(100 * (max(book_index - 1, 0) + fraction) / max(book_total, 1))))


class ProgressTracker:
    def __init__(self, order, save):
        self.order, self.save = order, save

    def __call__(self, stage, label, **details):
        now = datetime.now(timezone.utc).isoformat()
        prior = self.order.get("generation_progress") or {}
        progress = {**prior, **details, "stage": stage, "label": label,
            "updated_at": now, "started_at": prior.get("started_at", now), "error": None}
        progress["percent"] = progress_percent(stage, progress.get("book_index", 1),
            progress.get("book_total", 1), progress.get("page_index", 0), progress.get("page_total", 10))
        history = list(prior.get("history") or [])
        history.append({"at": now, "stage": stage, "message": label})
        progress["history"] = history[-80:]
        self.save({"generation_progress": progress})
        self.order["generation_progress"] = progress


def failed_progress(order, error):
    prior = order.get("generation_progress") or {}
    now = datetime.now(timezone.utc).isoformat()
    message = safe_error(error)
    return {**prior, "stage": "error", "failed_stage": prior.get("stage", "assets"),
        "label": "Production interrompue", "error": message, "updated_at": now,
        "history": [*(prior.get("history") or []), {"at": now, "stage": "error", "message": message}][-80:]}
