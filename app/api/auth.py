from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, model_validator

from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr | None = None
    password: str
    phone_number: str | None = None

    @model_validator(mode="after")
    def validate_contact(self):
        if not (self.email or self.phone_number):
            raise ValueError("email or phone_number is required")
        return self


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr | None = None
    phone_number: str | None = None
    token: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None
    password: str

    @model_validator(mode="after")
    def validate_contact(self):
        if not (self.email or self.phone_number):
            raise ValueError("email or phone_number is required")
        return self


@router.post("/register", response_model=UserResponse)
async def register(req: RegisterRequest, svc: AuthService = Depends()):
    user = await svc.register(
        name=req.name,
        email=req.email,
        password=req.password,
        phone_number=req.phone_number,
    )
    return user


@router.post("/login", response_model=UserResponse)
async def login(req: LoginRequest, svc: AuthService = Depends()):
    user = await svc.authenticate(email=req.email, phone_number=req.phone_number, password=req.password)
    return user
