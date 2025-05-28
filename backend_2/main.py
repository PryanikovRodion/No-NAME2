from fastapi import FastAPI
from database.db import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware
from routes.base import app as base_router
from routes.buyer import app as buyer_router
from routes.seller import app as seller_router

create_db_and_tables()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(buyer_router, prefix="/buyer", tags=["buyer"])
app.include_router(base_router, prefix="/base", tags=["base"])
app.include_router(seller_router, prefix="/seller", tags=["seller"])
