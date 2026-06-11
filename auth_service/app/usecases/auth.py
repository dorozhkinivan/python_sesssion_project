from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.users import UsersRepository
from app.schemas.auth import TokenResponse


class AuthUseCase:
    def __init__(self, users_repo: UsersRepository):
        self._users_repo = users_repo

    async def register(self, email: str, password: str) -> TokenResponse:
        existing = await self._users_repo.get_by_email(email)
        if existing is not None:
            raise UserAlreadyExistsError()

        hashed = hash_password(password)
        user = await self._users_repo.create(email=email, password_hash=hashed)

        token = create_access_token(sub=str(user.id), role=user.role)
        return TokenResponse(access_token=token)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._users_repo.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        token = create_access_token(sub=str(user.id), role=user.role)
        return TokenResponse(access_token=token)

    async def me(self, user_id: int) -> User:
        user = await self._users_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return user
