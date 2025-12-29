from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from app.api.chat import router as chat_router
from app.api.rag import router as rag_router
from app.api.auth import router as auth_router
from app.security.middleware import attach_user_from_token

app = FastAPI(title="Minimal Layered FastAPI")


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

app.middleware("http")(attach_user_from_token)

app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(auth_router)
