import uuid
from datetime import datetime

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from mathutrice import models
from mathutrice.fonctions_python.main import REFERENTIEL
from mathutrice.fonctions_python.seed import seed_if_empty
from mathutrice.fonctions_python.session_generator import init_progressions_for_user


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def rows(session, model):
    return session.exec(select(model)).all()


def test_seeds_every_notion_of_the_referentiel(session):
    seed_if_empty(session)

    notions = {n.referentiel_key: n for n in rows(session, models.Notion)}

    assert set(notions) == set(REFERENTIEL)
    for key, notion in notions.items():
        assert notion.title == REFERENTIEL[key]["notion_nom"]
        assert isinstance(notion.notion_id, uuid.UUID)
        assert notion.description


def test_seeds_every_skill_under_its_notion(session):
    seed_if_empty(session)

    notion_key = {n.notion_id: n.referentiel_key for n in rows(session, models.Notion)}
    competences = rows(session, models.Competence)

    expected = {
        c["code"]: (key, c["nom"], c["niveau"])
        for key, notion in REFERENTIEL.items()
        for c in notion["competences"]
    }
    actual = {
        c.referentiel_code: (notion_key[c.notion_id], c.title, c.level)
        for c in competences
    }
    assert actual == expected


def test_seeds_one_user_per_role_with_the_right_domain(session):
    seed_if_empty(session)

    users = {u.role: u for u in rows(session, models.User)}

    assert set(users) == {"Student", "Teacher", "Admin"}
    assert users["Student"].email.endswith("@epfedu.fr")
    assert users["Teacher"].email.endswith("@epf.fr")
    assert users["Admin"].email.endswith("@epf.fr")
    assert len(rows(session, models.User)) == 3


def test_seeded_student_gets_a_progression_for_every_skill(session):
    seed_if_empty(session)
    student = next(u for u in rows(session, models.User) if u.role == "Student")

    init_progressions_for_user(student.sso_id, session)

    assert len(rows(session, models.Progression)) == len(
        rows(session, models.Competence)
    )


def test_reports_whether_it_seeded(session):
    assert seed_if_empty(session) is True
    assert seed_if_empty(session) is False


def test_second_call_changes_nothing(session):
    seed_if_empty(session)
    before = [len(rows(session, m)) for m in (models.Notion, models.Competence, models.User)]

    seed_if_empty(session)

    after = [len(rows(session, m)) for m in (models.Notion, models.Competence, models.User)]
    assert after == before


def test_does_nothing_when_a_user_already_exists(session):
    session.add(
        models.User(
            sso_id=uuid.uuid4(),
            created_at=datetime.utcnow(),
            role="Student",
            email="someone@epfedu.fr",
            name="Someone",
        )
    )
    session.commit()

    assert seed_if_empty(session) is False

    assert len(rows(session, models.User)) == 1
    assert rows(session, models.Notion) == []


def test_does_nothing_when_a_notion_already_exists(session):
    session.add(
        models.Notion(
            notion_id=uuid.uuid4(),
            referentiel_key="custom",
            title="Custom",
            description="Already there",
        )
    )
    session.commit()

    assert seed_if_empty(session) is False

    assert len(rows(session, models.Notion)) == 1
    assert rows(session, models.User) == []


def test_application_startup_seeds_an_empty_database():
    from fastapi.testclient import TestClient

    from mathutrice.app import app, engine

    with TestClient(app):
        with Session(engine) as session:
            assert {u.role for u in rows(session, models.User)} == {
                "Student",
                "Teacher",
                "Admin",
            }
            assert len(rows(session, models.Notion)) == len(REFERENTIEL)
