"""Add CASCADE delete to all foreign keys — fix NOT NULL constraint error on course deletion."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RELATION_TYPES = ("prerequisite", "contains", "causal", "related")


def upgrade() -> None:
    # SQLite does not support ALTER TABLE ADD CONSTRAINT, so we must rebuild tables.
    # 1. generation_progress (depends on courses)
    op.execute("DROP TABLE IF EXISTS generation_progress")
    op.create_table(
        "generation_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id"),
    )

    # 2. content_modules (depends on chapters)
    op.execute("DROP TABLE IF EXISTS content_modules")
    op.create_table(
        "content_modules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("modal_type", sa.String(length=30), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. knowledge_edges (depends on courses, knowledge_nodes)
    op.execute("DROP TABLE IF EXISTS knowledge_edges")
    op.create_table(
        "knowledge_edges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("source_node_id", sa.Integer(), nullable=False),
        sa.Column("target_node_id", sa.Integer(), nullable=False),
        sa.Column("relation_type", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_node_id"], ["knowledge_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_node_id"], ["knowledge_nodes.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            f"relation_type IN {RELATION_TYPES}",
            name="ck_knowledge_edges_relation_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. knowledge_nodes (depends on courses)
    op.execute("DROP TABLE IF EXISTS knowledge_nodes")
    op.create_table(
        "knowledge_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. chapters (depends on courses)
    op.execute("DROP TABLE IF EXISTS chapters")
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("knowledge_node_ids", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Rebuild tables without CASCADE
    op.execute("DROP TABLE IF EXISTS chapters")
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("knowledge_node_ids", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("DROP TABLE IF EXISTS knowledge_nodes")
    op.create_table(
        "knowledge_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("DROP TABLE IF EXISTS knowledge_edges")
    op.create_table(
        "knowledge_edges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("source_node_id", sa.Integer(), nullable=False),
        sa.Column("target_node_id", sa.Integer(), nullable=False),
        sa.Column("relation_type", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["source_node_id"], ["knowledge_nodes.id"]),
        sa.ForeignKeyConstraint(["target_node_id"], ["knowledge_nodes.id"]),
        sa.CheckConstraint(
            f"relation_type IN {RELATION_TYPES}",
            name="ck_knowledge_edges_relation_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("DROP TABLE IF EXISTS content_modules")
    op.create_table(
        "content_modules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("modal_type", sa.String(length=30), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("DROP TABLE IF EXISTS generation_progress")
    op.create_table(
        "generation_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id"),
    )
