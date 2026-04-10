from __future__ import annotations

from app.api.errors import forbidden
from app.auth.schemas import AuthenticatedRequestContext


ROLE_PERMISSION_MAP: dict[str, list[str]] = {
    "business_owner": [
        "tenant.*",
        "organisation.*",
        "business.*",
        "site.*",
        "membership.*",
        "subscription.*",
        "finance.*",
        "integration.*",
        "pricing.*",
    ],
    "organisation_admin": [
        "organisation.read",
        "organisation.manage",
        "business.read",
        "business.manage",
        "site.read",
        "site.manage",
        "membership.read",
        "membership.manage",
        "subscription.read",
        "subscription.manage",
        "finance.read",
        "finance.manage",
    ],
}


class AuthorizationService:
    """Central authorization policy entrypoint for Module 00.

    Current implementation now supports:
    - platform_owner as a distinct non-tenant principal with global wildcard access
    - tenant membership-based permission union
    - simple wildcard permissions such as `tenant.*`
    """

    def list_effective_permissions(self, *, context: AuthenticatedRequestContext) -> list[str]:
        principal_type = str(context.user.get("principal_type", "")).strip()
        if principal_type == "platform_owner":
            return ["*"]

        effective: set[str] = set()
        for membership in context.memberships:
            role = str(membership.get("role", "")).strip()
            for permission in ROLE_PERMISSION_MAP.get(role, []):
                effective.add(permission)

        return sorted(effective)

    def require_platform_owner(self, *, context: AuthenticatedRequestContext) -> None:
        principal_type = str(context.user.get("principal_type", "")).strip()
        if principal_type != "platform_owner":
            raise forbidden("Platform owner access required", reason_code="platform_owner_required")

    @staticmethod
    def _permission_matches(effective_permission: str, required_permission: str) -> bool:
        if effective_permission == "*" or effective_permission == required_permission:
            return True
        if effective_permission.endswith("*"):
            prefix = effective_permission[:-1]
            return required_permission.startswith(prefix)
        return False

    def require_permission(self, *, context: AuthenticatedRequestContext, permission: str) -> None:
        permissions = self.list_effective_permissions(context=context)
        if any(self._permission_matches(p, permission) for p in permissions):
            return
        raise forbidden(
            f"Missing required permission: {permission}",
            reason_code="permission_denied",
            context={"required_permission": permission},
        )


authorization_service = AuthorizationService()
