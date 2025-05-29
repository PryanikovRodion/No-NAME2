from fastapi import APIRouter, Depends, HTTPException
from utils import get_seller
from sqlmodel import Session
from database.db import get_session
from schems.posts import *

app = APIRouter()

@app.post("/add_product")
def add_product(product: CreateProduct, seller=Depends(get_seller), db: Session = Depends(get_session)):
    seller.add_product(db, product)
    return {"message": "Product added successfully"}

@app.get("/my_products", response_model=list[ProductFullInfo])
def get_my_products(seller=Depends(get_seller), db: Session = Depends(get_session)):
    return [ProductFullInfo.model_validate(product, from_attributes=True) for product in seller.products]

@app.get("/my_orders", response_model=list[OrderFullInfo])
def get_my_orders(seller=Depends(get_seller)):
    return [OrderFullInfo.model_validate(order, from_attributes=True) for order in seller.seller_orders]

@app.post("/my_orders/{order_id}/acknowledged")
def acknowledge_order(order_id: int, seller=Depends(get_seller), db: Session = Depends(get_session)):
    seller.order_acknowledged(db, order_id)
    return {"message": "Order acknowledged successfully"}

@app.post("/my_orders/{order_id}/shipped")
def ship_order(order_id: int, seller=Depends(get_seller), db: Session = Depends(get_session)):
    seller.order_shipped(db, order_id)
    return {"message": "Order shipped successfully"}

