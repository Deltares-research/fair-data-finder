import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from api.config import APISettings
from api.database.models import Group, GroupRole, GroupUserLink, Role, User
from sqlmodel import Session, create_engine, select
from stac_fastapi.types.config import Settings

_LOGGER = logging.getLogger("uvicorn.default")

ALL_DELTARES_GROUP = "All Deltares"


def run_migrations():
    config_path = Path(__file__).parent.parent.parent / "alembic.ini"
    alembic_cfg = Config(config_path)
    settings: APISettings = Settings.get()
    if settings.environment == "local":
        _LOGGER.info(
            f"Checking for unapplied DB migrations. Not running them. using config at {config_path}"
        )
        # command.check(alembic_cfg)
    else:
        _LOGGER.info("Running DB migrations")
        command.upgrade(alembic_cfg, "head")


def create_admin_users():
    settings: APISettings = Settings.get()
    engine = create_engine(settings.db_connection_url)
    if not settings.admin_users:
        return

    with Session(engine) as session:
        # create admin users
        admin_users = settings.admin_users.split(",")
        db_users: list[User] = []
        for admin_email in admin_users:
            # check if user already exists
            existing_user = session.exec(
                select(User).where(User.email == admin_email)
            ).first()
            if existing_user:
                _LOGGER.info(f"Admin user {admin_email} already exists")
                db_users.append(existing_user)
                continue
            _LOGGER.info(f"Creating admin user {admin_email}")
            db_user = User(email=admin_email, username=admin_email)
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            db_users.append(db_user)

        # create admin group
        # check if admin group already exists
        admin_group = session.exec(select(Group).where(Group.name == "admin")).first()
        if admin_group:
            _LOGGER.info("Admin group already exists")
            admin_group_users = [user.email for user in admin_group.users]
        else:
            _LOGGER.info("Creating admin group")
            admin_group_users = []
            admin_group = Group(name="admin", description="Admin group")
            session.add(admin_group)
            session.commit()
            session.refresh(admin_group)

        # add users to admin group
        for db_user in db_users:
            if db_user.email in admin_group_users:
                _LOGGER.info(f"User {db_user.email} already in admin group")
                continue
            _LOGGER.info(f"Adding user {db_user.email} to admin group")
            admin_group.users.append(db_user)
        session.commit()
        session.refresh(admin_group)

        # Assign admin role to admin group
        admin_role = session.exec(
            select(GroupRole).where(
                GroupRole.role == Role.ADMIN, GroupRole.group_id == admin_group.id
            )
        ).first()
        if admin_role:
            _LOGGER.info("Admin role already exists")
        else:
            _LOGGER.info("Creating admin role")
            admin_role = GroupRole(
                role=Role.ADMIN, group_id=admin_group.id, object=None
            )
            session.add(admin_role)
            session.commit()
            session.refresh(admin_role)
            _LOGGER.info("Admin role created")


def ensure_all_deltares_group(session: Session) -> Group:
    """Return the "All Deltares" group, creating it and its role if needed.

    The group has the whole-app data_producer role, so its members can add
    items to every collection and edit the items they created.
    """
    group = session.exec(select(Group).where(Group.name == ALL_DELTARES_GROUP)).first()
    if group is None:
        _LOGGER.info(f"Creating group {ALL_DELTARES_GROUP}")
        group = Group(
            name=ALL_DELTARES_GROUP,
            description="Every user; can add items and edit their own items",
        )
        session.add(group)
        session.commit()
        session.refresh(group)

    role = session.exec(
        select(GroupRole).where(
            GroupRole.group_id == group.id,
            GroupRole.role == Role.DATA_PRODUCER,
            GroupRole.object.is_(None),
        )
    ).first()
    if role is None:
        _LOGGER.info(f"Assigning data_producer role to group {ALL_DELTARES_GROUP}")
        session.add(GroupRole(group_id=group.id, role=Role.DATA_PRODUCER, object=None))
        session.commit()
    return group


def add_to_all_deltares_group(session: Session, email: str) -> None:
    """Add a user to the "All Deltares" group if not already a member."""
    group = ensure_all_deltares_group(session)
    if session.get(GroupUserLink, (group.id, email)) is None:
        _LOGGER.info(f"Adding user {email} to group {ALL_DELTARES_GROUP}")
        session.add(GroupUserLink(group_id=group.id, user_email=email))
        session.commit()


def create_all_deltares_group() -> None:
    """Create the "All Deltares" group and add all existing users to it."""
    settings: APISettings = Settings.get()
    engine = create_engine(settings.db_connection_url)
    with Session(engine) as session:
        group = ensure_all_deltares_group(session)
        members = set(
            session.exec(
                select(GroupUserLink.user_email).where(
                    GroupUserLink.group_id == group.id
                )
            ).all()
        )
        for email in session.exec(select(User.email)).all():
            if email not in members:
                session.add(GroupUserLink(group_id=group.id, user_email=email))
        session.commit()
