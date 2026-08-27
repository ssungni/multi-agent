import pytest
from sqlalchemy.exc import IntegrityError

from src.auth.constants import UserStatus
from src.auth.repository import UserRepository


def make_user(repo, email="user@example.com", phone="010-1234-5678"):
    return repo.create(name="홍길동", email=email, phone=phone, password_hash="hashed")


def test_create_and_get_by_email(db_session):
    repo = UserRepository(db_session)
    created = make_user(repo)

    found = repo.get_by_email("user@example.com")
    assert found is not None
    assert found.id == created.id
    assert found.status == UserStatus.PENDING.value


def test_email_uniqueness_enforced(db_session):
    repo = UserRepository(db_session)
    make_user(repo, email="dup@example.com", phone="010-1111-1111")
    with pytest.raises(IntegrityError):
        make_user(repo, email="dup@example.com", phone="010-2222-2222")


def test_phone_uniqueness_enforced(db_session):
    repo = UserRepository(db_session)
    make_user(repo, email="a@example.com", phone="010-9999-9999")
    with pytest.raises(IntegrityError):
        make_user(repo, email="b@example.com", phone="010-9999-9999")


def test_get_by_email_case_insensitive(db_session):
    repo = UserRepository(db_session)
    make_user(repo, email="Mixed@Example.com", phone="010-3333-3333")
    found = repo.get_by_email("mixed@example.com")
    assert found is not None


def test_update_status(db_session):
    repo = UserRepository(db_session)
    user = make_user(repo)
    repo.update_status(user, UserStatus.ACTIVE.value)
    assert repo.get_by_email("user@example.com").status == UserStatus.ACTIVE.value


def test_update_last_login(db_session):
    repo = UserRepository(db_session)
    user = make_user(repo)
    assert user.last_login_at is None
    repo.update_last_login(user)
    assert repo.get_by_id(user.id).last_login_at is not None


def test_get_by_id_missing_returns_none(db_session):
    repo = UserRepository(db_session)
    assert repo.get_by_id(999999) is None
