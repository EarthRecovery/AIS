from app.services.chat_service import ChatService
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.security.jwt import create_access_token
import hashlib

from app.db import get_db
from app.models.user import User


def _hash_password(password: str) -> str:
    # Simple SHA256 hashing; replace with stronger hashing if needed.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def register(self, name: str, email: str | None, password: str, phone_number: str | None = None) -> User:
        # Check if user already exists by email or phone.
        if email is None and phone_number is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either email or phone number must be provided",
            )
        conditions = []
        if email is not None:
            conditions.append(User.email == email)
        if phone_number is not None:
            conditions.append(User.phone_number == phone_number)
        stmt = select(User).where(*conditions) if len(conditions) == 1 else select(User).where(
            conditions[0] | conditions[1]
        )
        existing = await self.db.execute(stmt)
        user = existing.scalars().first()
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists with this email or phone number",
            )

        hashed = _hash_password(password)
        new_user = User(
            name=name,
            email=email,
            phone_number=phone_number,
            hashed_password=hashed,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        new_user.token = await self.create_jwt_token(new_user.id)
        chatService = ChatService(db=self.db)
        await chatService.start_new_chat(new_user.id)
        return new_user

    async def authenticate(self, email: str | None = None, phone_number: str | None = None, password: str = None) -> User:
        if email is None and phone_number is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either email or phone number must be provided",
            )
        conditions = []
        if email is not None:
            conditions.append(User.email == email)
        if phone_number is not None:
            conditions.append(User.phone_number == phone_number)
        stmt = select(User).where(*conditions) if len(conditions) == 1 else select(User).where(
            conditions[0] | conditions[1]
        )
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if user.hashed_password != _hash_password(password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        user.token = await self.create_jwt_token(user.id)
        return user
    
    async def create_jwt_token(self, user_id: int) -> str:
        # Placeholder function for JWT token creation
        return create_access_token(sub=str(user_id))
