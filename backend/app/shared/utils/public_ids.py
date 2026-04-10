import ulid


def new_public_id(prefix: str) -> str:
    return f"{prefix}_{ulid.new()}"
