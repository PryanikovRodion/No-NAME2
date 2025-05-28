from fastapi import APIRouter, Depends, HTTPException
from utils import get_buyer
from sqlmodel import Session
from database.db import get_session
from schems.posts import CreateCartItem, CartItemsInfo, CreateOrder

app = APIRouter()

@app.post("/add_balance/{amount}")
def add_balance(amount: float, buyer=Depends(get_buyer), db: Session = Depends(get_session)):
    buyer.add_balance(db, amount)
    return {"message": "Balance added successfully", "new_balance": buyer.balance}

@app.post("/add_cart_items")
def add_cart_items(cart_item: CreateCartItem, buyer=Depends(get_buyer), db: Session = Depends(get_session)):
    buyer.add_cart_item(db, cart_item)
    return {"message": "Cart item added successfully"}

@app.get("/my_cart_items", response_model=list[CartItemsInfo])
def get_cart_items(buyer=Depends(get_buyer)):
    cart_items = buyer.cart_items
    if not cart_items:
        raise HTTPException(status_code=404, detail="No cart items found")
    return [CartItemsInfo.model_validate(item, from_attributes=True) for item in cart_items]

@app.post("/create_order")
def create_order(order: CreateOrder, buyer=Depends(get_buyer), db: Session = Depends(get_session)):
    buyer.create_order(db, order)
    return {"message": "Order created successfully"}

@app.get("/my_orders", response_model=list[CartItemsInfo])
def get_orders(buyer=Depends(get_buyer)):
    orders = buyer.orders
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")
    return [CartItemsInfo.model_validate(order, from_attributes=True) for order in orders]

@app.post("/my_orders/{order_id}/confirm")
def confirm_order(order_id: int, buyer=Depends(get_buyer), db: Session = Depends(get_session)):
    buyer.order_confirmed(db, order_id)
    return {"message": "Order confirmed successfully"}

@app.post("/my_orders/{order_id}/cancel")
def cancel_order(order_id: int, buyer=Depends(get_buyer), db: Session = Depends(get_session)):
    buyer.order_cancelled(db, order_id)
    return {"message": "Order cancelled successfully"}

@app.post("/my_orders/{order_id}/received")
def received_order(order_id: int, buyer=Depends(get_buyer), db: Session = Depends(get_session)):
    buyer.order_received(db, order_id)
    return {"message": "Order received successfully"}

@app.delete("/my_cart_items/{cart_item_id}")
def delete_cart_item(cart_item_id: int, buyer=Depends(get_buyer), db: Session = Depends(get_session)):
    buyer.delete_cart_item(db, cart_item_id)
    return {"message": "Cart item deleted successfully"}