from fastapi import FastAPI
from .routes import router


app = FastAPI(
    title="Organization API",
    description="API для управления организациями, телефонами и активностями",
    version="1.0.0",
)

app.include_router(router)