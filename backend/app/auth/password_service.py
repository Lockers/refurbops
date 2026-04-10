from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


_password_hasher = PasswordHasher()


class PasswordService:
    def hash_password(self, password: str) -> str:
        if not password or not password.strip():
            raise ValueError("Password must not be blank")
        return _password_hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return _password_hasher.verify(password_hash, password)
        except VerifyMismatchError:
            return False


password_service = PasswordService()
