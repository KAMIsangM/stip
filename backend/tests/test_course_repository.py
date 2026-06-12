"""Repository unit tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.repository.course_repository import CourseRepository
from app.repository.knowledge_repository import KnowledgeRepository
from app.repository.progress_repository import ProgressRepository
from app.repository.content_repository import ContentRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_course_repository_create_and_get(db_session):
    repo = CourseRepository(db_session)
    course = repo.create(title="Python 基础", description="入门课程", status="draft")

    assert course.id is not None
    assert course.title == "Python 基础"

    fetched = repo.get_by_id(course.id)
    assert fetched is not None
    assert fetched.title == "Python 基础"
    assert fetched.description == "入门课程"


def test_course_repository_list_and_chapters(db_session):
    repo = CourseRepository(db_session)
    course = repo.create(title="数据结构")
    repo.create_chapter(course.id, title="第一章", order=1)
    repo.create_chapter(course.id, title="第二章", order=2)

    courses = repo.list_all()
    assert len(courses) == 1

    chapters = repo.get_chapters_by_course_id(course.id)
    assert len(chapters) == 2
    assert chapters[0].title == "第一章"
    assert chapters[1].order == 2


def test_course_repository_update_and_delete(db_session):
    repo = CourseRepository(db_session)
    course = repo.create(title="旧标题")

    updated = repo.update(course.id, title="新标题", status="generating")
    assert updated is not None
    assert updated.title == "新标题"
    assert updated.status == "generating"

    assert repo.delete(course.id) is True
    assert repo.get_by_id(course.id) is None


def test_knowledge_repository_nodes_and_edges(db_session):
    course_repo = CourseRepository(db_session)
    knowledge_repo = KnowledgeRepository(db_session)
    course = course_repo.create(title="图谱测试")

    node_a = knowledge_repo.create_node(
        course.id, name="变量", node_type="concept", importance=0.8
    )
    node_b = knowledge_repo.create_node(course.id, name="函数", node_type="skill")
    edge = knowledge_repo.create_edge(
        course.id, node_a.id, node_b.id, relation_type="prerequisite"
    )

    nodes = knowledge_repo.list_nodes_by_course_id(course.id)
    edges = knowledge_repo.list_edges_by_course_id(course.id)
    assert len(nodes) == 2
    assert len(edges) == 1
    assert edges[0].id == edge.id


def test_progress_repository(db_session):
    course_repo = CourseRepository(db_session)
    progress_repo = ProgressRepository(db_session)
    course = course_repo.create(title="进度测试")

    progress = progress_repo.create(
        course.id, status="pending", current_step=0, total_steps=10
    )
    assert progress.course_id == course.id

    updated = progress_repo.update(
        course.id, status="outline_generating", current_step=1
    )
    assert updated is not None
    assert updated.status == "outline_generating"
    assert updated.current_step == 1


def test_content_repository(db_session):
    course_repo = CourseRepository(db_session)
    content_repo = ContentRepository(db_session)
    course = course_repo.create(title="内容测试")
    chapter = course_repo.create_chapter(course.id, title="章节1", order=1)

    module = content_repo.create(
        chapter.id,
        modal_type="ppt",
        content_json='{"slides": []}',
        file_path="courses/1/ppt/ch1.pptx",
    )
    modules = content_repo.list_by_chapter_id(chapter.id)
    assert len(modules) == 1
    assert modules[0].modal_type == "ppt"
    assert module.id == modules[0].id
