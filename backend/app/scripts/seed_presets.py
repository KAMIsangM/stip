"""Seed knowledge-graph presets into the database on first startup.

Usage:
    python -m app.scripts.seed_presets

Or imported in main.py startup event.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.core.database import SessionLocal
from app.models import KnowledgeEdge, KnowledgeNode

logger = logging.getLogger(__name__)

PRESETS_DIR = Path(__file__).resolve().parents[1] / "data" / "presets"

# ---------------------------------------------------------------------------
# predefined presets that serve as "global templates" — course_id=0
# ---------------------------------------------------------------------------


def _is_already_seeded() -> bool:
    """Check if preset nodes already exist (course_id=0)."""
    db = SessionLocal()
    try:
        return db.query(KnowledgeNode).filter(KnowledgeNode.course_id == 0).count() > 0
    finally:
        db.close()


def seed_presets() -> None:
    """Import all preset JSON files into course_id=0 as templates."""
    if _is_already_seeded():
        logger.info("Presets already seeded, skipping.")
        return

    if not PRESETS_DIR.exists():
        logger.warning("Presets directory not found: %s", PRESETS_DIR)
        return

    db = SessionLocal()
    try:
        for preset_file in sorted(PRESETS_DIR.glob("preset_*.json")):
            with open(preset_file, encoding="utf-8") as f:
                data = json.load(f)

            preset_name = data.get("name", preset_file.stem)
            logger.info("Seeding preset: %s", preset_name)

            id_map: dict[int, int] = {}

            for nd in data.get("nodes", []):
                node = KnowledgeNode(
                    course_id=0,  # global template
                    name=nd["name"],
                    type=nd.get("type", "概念"),
                    importance=nd.get("importance", 0.5),
                    description=nd.get("description"),
                )
                db.add(node)
                db.flush()
                id_map[nd["id"]] = node.id

            for ed in data.get("edges", []):
                src = id_map.get(ed["source_node_id"])
                tgt = id_map.get(ed["target_node_id"])
                if src is None or tgt is None:
                    logger.warning("  Skipping edge: missing node ref")
                    continue
                edge = KnowledgeEdge(
                    course_id=0,
                    source_node_id=src,
                    target_node_id=tgt,
                    relation_type=ed.get("relation_type", "related"),
                )
                db.add(edge)

        db.commit()
        logger.info("Preset seeding complete.")
    except Exception:
        db.rollback()
        logger.exception("Preset seeding failed.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_presets()
