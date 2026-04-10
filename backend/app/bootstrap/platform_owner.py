from pymongo.asynchronous.database import AsyncDatabase

from app.auth.password_service import password_service
from app.auth.repository import AuthRepository
from app.config import Settings
from app.logging import get_logger


logger = get_logger(component="platform_owner_bootstrap")


async def ensure_platform_owner_seeded(*, database: AsyncDatabase, settings: Settings) -> None:
    repository = AuthRepository(database)
    existing_users = await repository.list_platform_owner_users()

    if len(existing_users) > 1:
        raise RuntimeError("Multiple platform_owner users found. RefurbOps allows only one platform_owner.")

    expected_email = settings.platform_owner_email.lower().strip()
    initial_password = settings.platform_owner_initial_password.strip()

    if len(existing_users) == 1:
        existing_user = existing_users[0]
        existing_email = str(existing_user.get("email", "")).lower().strip()
        if existing_email != expected_email:
            raise RuntimeError(
                "Existing platform_owner email does not match PLATFORM_OWNER_EMAIL. "
                f"Found {existing_email!r}, expected {expected_email!r}."
            )

        existing_credential = await repository.get_credentials_for_user(
            user_public_id=str(existing_user["public_id"])
        )
        if existing_credential is None:
            if not initial_password:
                logger.warning(
                    "platform_owner.credential_missing_and_not_repaired_missing_password",
                    email=existing_email,
                )
                return
            await repository.create_local_password_credentials(
                user_public_id=str(existing_user["public_id"]),
                password_hash=password_service.hash_password(initial_password),
            )
            logger.info("platform_owner.credential_repaired", email=existing_email)
            return

        logger.info("platform_owner.seed_present", email=existing_email)
        return

    if not initial_password:
        logger.warning(
            "platform_owner.seed_skipped_missing_password",
            email=settings.platform_owner_email,
        )
        return

    await repository.create_platform_owner(
        email=settings.platform_owner_email,
        password_hash=password_service.hash_password(initial_password),
        mfa_required=settings.platform_owner_require_mfa,
    )
    logger.info("platform_owner.seed_created", email=settings.platform_owner_email)
