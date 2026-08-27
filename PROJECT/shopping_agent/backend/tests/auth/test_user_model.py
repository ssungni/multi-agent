from src.auth.constants import UserStatus
from src.auth.models import User


def test_user_table_columns():
    columns = User.__table__.columns.keys()
    assert columns == [
        "id",
        "name",
        "email",
        "phone",
        "password_hash",
        "status",
        "created_at",
        "updated_at",
        "last_login_at",
    ]


def test_user_unique_constraints():
    unique_cols = {c.name for c in User.__table__.columns if c.unique}
    assert unique_cols == {"email", "phone"}


def test_user_default_status_is_pending():
    assert User.__table__.columns["status"].default.arg == UserStatus.PENDING.value


def test_user_status_check_constraint_values():
    check = next(
        c for c in User.__table__.constraints if c.name == "ck_users_status"
    )
    assert "PENDING" in str(check.sqltext) and "WITHDRAWN" in str(check.sqltext)
