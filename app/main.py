from fastapi import FastAPI
from app.database import init_db, close_db
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import user


app = FastAPI()

# Rest of your code remains the same
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/")
async def root():
    return {"message": "Welcome to the X-sell Shopping API"}

