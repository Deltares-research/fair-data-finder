from api.core.startup import ALL_DELTARES_GROUP, create_all_deltares_group
from api.database.models import Group, GroupRole, GroupUserLink, Role, User
from api.extensions.core.sso_auth_extension import add_user
from fastapi import FastAPI
from fastapi_sso import OpenID
from sqlmodel import Session, select


def _group_state(db_session: Session) -> tuple[set[str], list[tuple[Role, str | None]]]:
    db_session.expire_all()
    group = db_session.exec(select(Group).where(Group.name == ALL_DELTARES_GROUP)).one()
    members = set(
        db_session.exec(
            select(GroupUserLink.user_email).where(GroupUserLink.group_id == group.id)
        ).all()
    )
    roles = [
        (role.role, role.object)
        for role in db_session.exec(
            select(GroupRole).where(GroupRole.group_id == group.id)
        ).all()
    ]
    return members, roles


def test_startup_adds_existing_users(app: FastAPI, user: User, db_session: Session):
    create_all_deltares_group()
    create_all_deltares_group()

    members, roles = _group_state(db_session)
    assert members == {user.email}
    assert roles == [(Role.DATA_PRODUCER, None)]


def test_login_adds_user(app: FastAPI, db_session: Session):
    openid = OpenID(email="new.user@deltares.nl", display_name="New User")
    add_user(openid)
    add_user(openid)

    members, roles = _group_state(db_session)
    assert members == {"new.user@deltares.nl"}
    assert roles == [(Role.DATA_PRODUCER, None)]
