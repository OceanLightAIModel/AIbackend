from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from database.database import engine, Base
from route.auth import auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
