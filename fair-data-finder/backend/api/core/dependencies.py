from typing import Annotated, Callable

from api.database.models import (
    GroupRole,
    GroupUserLink,
    ItemOwner,
    Permission,
    User,
    role_permissions,
)
from fastapi import Depends, HTTPException, Path
from sqlalchemy import func, or_
from sqlmodel import Session, select

from ..database.db import get_session
from ..extensions.core.sso_auth_extension import SSOAuthExtension

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(SSOAuthExtension.get_logged_user)]

# Whole-app roles grant these permissions in every collection.
# Item updates granted this way are limited to items the user created.
WHOLE_APP_ITEM_PERMISSIONS = {Permission.ItemCreate, Permission.ItemUpdate}


def get_user_collection_roles(
    session: Session, email: str, collection_id: str
) -> tuple[list[GroupRole], list[GroupRole]]:
    """Return the user's roles on a collection and the user's whole-app roles."""
    roles = session.exec(
        select(GroupRole)
        .join(GroupUserLink, GroupRole.group_id == GroupUserLink.group_id)
        .where(func.lower(GroupUserLink.user_email) == func.lower(email))
        .where(or_(GroupRole.object == collection_id, GroupRole.object.is_(None)))
    ).all()
    collection_roles = [role for role in roles if role.object is not None]
    whole_app_roles = [role for role in roles if role.object is None]
    return collection_roles, whole_app_roles


def roles_grant(roles: list[GroupRole], permission: Permission) -> bool:
    """Check if any of the roles includes the permission."""
    return any(permission in role_permissions[role.role] for role in roles)


def whole_app_roles_grant(roles: list[GroupRole], permission: Permission) -> bool:
    """Check if whole-app roles grant the permission inside a collection."""
    return permission in WHOLE_APP_ITEM_PERMISSIONS and roles_grant(roles, permission)


def is_item_owner(
    session: Session, email: str, collection_id: str, item_id: str
) -> bool:
    """Check if the user created the item."""
    owner = session.get(ItemOwner, (collection_id, item_id))
    return owner is not None and owner.owner_email.lower() == email.lower()


def user_has_global_permission(
    permission: Permission,
) -> Callable[[User, Session], None]:
    """Check if a user has a specific role for a given object."""

    def permission_dependency(
        user: User = Depends(SSOAuthExtension.get_logged_user),
        session: Session = Depends(get_session),
    ) -> None:
        # Get group roles for the user in a single query using a join
        group_roles = session.exec(
            select(GroupRole)
            .join(GroupUserLink, GroupRole.group_id == GroupUserLink.group_id)
            .where(
                func.lower(GroupUserLink.user_email) == func.lower(user.email),
                GroupRole.object.is_(None),
            )
        ).all()

        for group_role in group_roles:
            if permission in role_permissions[group_role.role]:
                return
        raise HTTPException(
            status_code=403,
            detail=f"User {user.email} does not have permission '{permission.value}'",
        )

    return permission_dependency


def user_has_collection_permission(
    permission: Permission,
) -> Callable[[User, Session], None]:
    """Check if a user has a permission on a collection.

    Roles on the collection itself count, and so do whole-app roles for
    the permissions in ``WHOLE_APP_ITEM_PERMISSIONS``.
    """

    def permission_dependency(
        collection_id: Annotated[str, Path()],
        user: User = Depends(SSOAuthExtension.get_logged_user),
        session: Session = Depends(get_session),
    ) -> None:
        collection_roles, whole_app_roles = get_user_collection_roles(
            session, user.email, collection_id
        )
        if roles_grant(collection_roles, permission) or whole_app_roles_grant(
            whole_app_roles, permission
        ):
            return
        raise HTTPException(
            status_code=403,
            detail=f"User {user.email} does not have permission {permission.value} on collection {collection_id}",
        )

    return permission_dependency


def user_can_update_item() -> Callable[[str, str, User, Session], None]:
    """Check if a user may update an item.

    A role on the collection allows editing every item in it. A whole-app
    role only allows editing items the user created.
    """

    def permission_dependency(
        collection_id: Annotated[str, Path()],
        item_id: Annotated[str, Path()],
        user: User = Depends(SSOAuthExtension.get_logged_user),
        session: Session = Depends(get_session),
    ) -> None:
        permission = Permission.ItemUpdate
        collection_roles, whole_app_roles = get_user_collection_roles(
            session, user.email, collection_id
        )
        if roles_grant(collection_roles, permission):
            return
        if not whole_app_roles_grant(whole_app_roles, permission):
            raise HTTPException(
                status_code=403,
                detail=f"User {user.email} does not have permission {permission.value} on collection {collection_id}",
            )
        if not is_item_owner(session, user.email, collection_id, item_id):
            raise HTTPException(
                status_code=403,
                detail=f"User {user.email} can only edit items they created",
            )

    return permission_dependency