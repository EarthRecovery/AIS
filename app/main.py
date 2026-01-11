from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import traceback
load_dotenv()

from app.api.chat import router as chat_router
from app.api.rag import router as rag_router
from app.api.auth import router as auth_router
from app.api.role import router as role_router
from app.security.middleware import attach_user_from_token

app = FastAPI(title="Minimal Layered FastAPI")

app.middleware("http")(attach_user_from_token)

# Global fallback to prevent unhandled exceptions from bubbling and killing responses
@app.middleware("http")
async def catch_unhandled_exceptions(request, call_next):
    try:
        return await call_next(request)
    except HTTPException:
        # Let FastAPI handle HTTPException as-is
        raise
    except Exception as exc:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://18.170.57.90:5173",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(auth_router)
app.include_router(role_router)
