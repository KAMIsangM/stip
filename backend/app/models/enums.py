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
    概念 = "概念"
    技能 = "技能"
    记忆 = "记忆"
    实践 = "实践"
    综合 = "综合"


class ModalType(str, enum.Enum):
    TEXT = "text"
    QUIZ = "quiz"
    PPT = "ppt"
    NARRATION = "narration"
    AUDIO = "audio"
    MINDMAP = "mindmap"
    INTERACTIVE_HTML = "interactive_html"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class ProgressStatus(str, enum.Enum):
    PENDING = "pending"
    OUTLINE_GENERATING = "outline_generating"
    CONTENT_GENERATING = "content_generating"
    DONE = "done"
    FAILED = "failed"
