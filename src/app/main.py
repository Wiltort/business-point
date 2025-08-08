from fastapi import FastAPI, Depends
from .db import get_db


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None, db: Session = Depends(get_db)):
    return {"item_id": item_id, "q": q}

