from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, model_validator
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security.jwt import get_current_user
from modules.auth.service import AuthService
from storage.db import get_db
from storage.models.llm_log import LLMLog
from storage.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


async def _load_user(user_id: str, db: AsyncSession) -> User | None:
    try:
        return await db.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


async def require_admin(user_id: str = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)) -> User:
    """需要 role == 'admin'。"""
    user = await _load_user(user_id, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return user


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


# ================= 当前用户 / 管理员 LLM 调用日志 =================
@router.get("/me")
async def me(user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await _load_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": user.id, "name": user.name, "email": user.email,
            "role": user.role, "is_admin": user.role == "admin"}


def _preview(s, n=160):
    s = s or ""
    return s[:n] + ("…" if len(s) > n else "")


@router.get("/llm-logs")
async def list_llm_logs(limit: int = 50, offset: int = 0, agent: str | None = None,
                        _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = select(LLMLog).order_by(LLMLog.id.desc())
    if agent:
        q = q.where(LLMLog.agent == agent)
    rows = (await db.execute(q.limit(min(limit, 200)).offset(max(offset, 0)))).scalars().all()
    cq = select(func.count(LLMLog.id))
    if agent:
        cq = cq.where(LLMLog.agent == agent)
    total = (await db.execute(cq)).scalar() or 0
    return {"total": total, "logs": [{
        "id": r.id, "agent": r.agent, "model": r.model, "ok": r.ok,
        "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
        "total_tokens": r.total_tokens, "duration_ms": r.duration_ms,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "prompt_preview": _preview(r.prompt), "response_preview": _preview(r.response),
        "error": r.error,
    } for r in rows]}


@router.get("/llm-logs/{log_id}")
async def get_llm_log(log_id: int, _admin: User = Depends(require_admin),
                      db: AsyncSession = Depends(get_db)):
    r = await db.get(LLMLog, log_id)
    if not r:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": r.id, "agent": r.agent, "model": r.model, "ok": r.ok, "error": r.error,
            "prompt": r.prompt, "response": r.response,
            "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
            "total_tokens": r.total_tokens, "duration_ms": r.duration_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None}


@router.delete("/llm-logs")
async def clear_llm_logs(_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(LLMLog))
    await db.commit()
    return {"ok": True}
