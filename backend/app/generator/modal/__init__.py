"""Modal generator registry."""

from app.generator.modal.interactive_generator import InteractiveGenerator
from app.generator.modal.mindmap_generator import MindMapGenerator
from app.generator.modal.ppt_generator import PPTGenerator
from app.generator.modal.quiz_generator import QuizGenerator
from app.generator.modal.text_generator import TextGenerator

# Registry: modal_type → Generator class
_MODAL_REGISTRY: dict[str, type] = {
    "text": TextGenerator,
    "quiz": QuizGenerator,
    "ppt": PPTGenerator,
    "mindmap": MindMapGenerator,
    "interactive_html": InteractiveGenerator,
}

__all__ = [
    "TextGenerator",
    "QuizGenerator",
    "PPTGenerator",
    "MindMapGenerator",
    "InteractiveGenerator",
    "_MODAL_REGISTRY",
]
