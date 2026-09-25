import uuid
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, select

from mathutrice import models
from mathutrice.app import cleanup_old_conversations, engine

NOW = datetime(2026, 9, 25, 12, 0, 0)


@pytest.fixture
def session():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def user(session):
    user = models.User(
        sso_id=uuid.uuid4(),
        created_at=NOW,
        role="Student",
        email=f"{uuid.uuid4()}@epfedu.fr",
        name="Student",
    )
    session.add(user)
    session.commit()
    return user


def add_conversation(session, user, started_ago, message_agos):
    conversation = models.Conversation(
        conversation_id=uuid.uuid4(),
        title="Conversation",
        status="active",
        started_at=NOW - started_ago,
        updated_at=NOW - started_ago,
        sso_id=user.sso_id,
    )
    session.add(conversation)
    for ago in message_agos:
        session.add(
            models.Message(
                message_id=uuid.uuid4(),
                role="user",
                content="Bonjour",
                sent_at=NOW - ago,
                conversation_id=conversation.conversation_id,
            )
        )
    session.commit()
    return conversation.conversation_id


def conversation_exists(session, conversation_id):
    return (
        session.exec(
            select(models.Conversation).where(
                models.Conversation.conversation_id == conversation_id
            )
        ).first()
        is not None
    )


def messages_of(session, conversation_id):
    return session.exec(
        select(models.Message).where(models.Message.conversation_id == conversation_id)
    ).all()


def test_keeps_a_conversation_started_long_ago_but_active_recently(session, user):
    conversation_id = add_conversation(
        session, user, started_ago=timedelta(hours=25), message_agos=[timedelta(hours=1)]
    )

    cleanup_old_conversations(now=NOW)

    session.expire_all()
    assert conversation_exists(session, conversation_id)
    assert len(messages_of(session, conversation_id)) == 1


def test_deletes_a_conversation_and_its_messages_once_idle_for_over_24_hours(session, user):
    conversation_id = add_conversation(
        session,
        user,
        started_ago=timedelta(hours=30),
        message_agos=[timedelta(hours=30), timedelta(hours=25)],
    )

    cleanup_old_conversations(now=NOW)

    session.expire_all()
    assert not conversation_exists(session, conversation_id)
    assert messages_of(session, conversation_id) == []


def test_keeps_a_conversation_whose_last_message_is_just_under_24_hours_old(session, user):
    conversation_id = add_conversation(
        session,
        user,
        started_ago=timedelta(hours=40),
        message_agos=[timedelta(hours=23, minutes=59)],
    )

    cleanup_old_conversations(now=NOW)

    session.expire_all()
    assert conversation_exists(session, conversation_id)


def test_a_conversation_without_messages_is_counted_from_when_it_started(session, user):
    old = add_conversation(session, user, started_ago=timedelta(hours=25), message_agos=[])
    recent = add_conversation(session, user, started_ago=timedelta(hours=2), message_agos=[])

    cleanup_old_conversations(now=NOW)

    session.expire_all()
    assert not conversation_exists(session, old)
    assert conversation_exists(session, recent)
