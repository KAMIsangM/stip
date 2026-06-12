import enum


class RelationType(str, enum.Enum):
    """Unified SRS/HLD relation types — see TECH-001."""

    PREREQUISITE = "prerequisite"  # 前驱后继
    CONTAINS = "contains"  # 包含
    CAUSAL = "causal"  # 因果
    RELATED = "related"  # 关联


class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    DONE = "done"
    FAILED = "failed"


class NodeType(str, enum.Enum):
    CONCEPT = "concept"
    SKILL = "skill"
    MEMORY = "memory"


class ModalType(str, enum.Enum):
    TEXT = "text"
    QUIZ = "quiz"
    PPT = "ppt"
    NARRATION = "narration"
    MINDMAP = "mindmap"
    INTERACTIVE_HTML = "interactive_html"


class ProgressStatus(str, enum.Enum):
    PENDING = "pending"
    OUTLINE_GENERATING = "outline_generating"
    CONTENT_GENERATING = "content_generating"
    DONE = "done"
    FAILED = "failed"
