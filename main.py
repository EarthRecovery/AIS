from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import traceback
load_dotenv()

from modules.chat.router import router as chat_router
from modules.rag.router import router as rag_router
from modules.auth.router import router as auth_router
from modules.role.router import router as role_router
from modules.communication.router import router as communication_router
from modules.communication.world_router import router as world_router
from core.security.middleware import attach_user_from_token

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
        "http://18.170.57.90:8100",
        "http://13.134.76.110:5173",
        "http://13.134.76.110:8100",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8100",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(auth_router)
app.include_router(role_router)
app.include_router(communication_router)
app.include_router(world_router)
