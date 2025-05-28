from fastapi import APIRouter, Depends, HTTPException
from schems.posts import CreateUser, AuthUser, Token, ProductInfo, UserInfo
from database.db import get_session
from database.models import User, Product
from sqlmodel import Session
from utils import get_curent_user

app = APIRouter()

@app.post("/registration")
def registration(user: CreateUser, db: Session = Depends(get_session)):
    User.create_user(db, user)

@app.post("/token", response_model=Token)
def token(auth_user: AuthUser, db: Session = Depends(get_session)):
    return Token(access_token=User.get_token(db, auth_user))

@app.get("/product/{product_id}", response_model=ProductInfo)
def get_product(product_id: int, db: Session = Depends(get_session)):
    product = ProductInfo.model_validate(db.get(Product, product_id), from_attributes=True)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/products", response_model=list[ProductInfo])
def get_products(db: Session = Depends(get_session)):
    products = db.exec(Product.select()).all()
    return [ProductInfo.model_validate(product, from_attributes=True) for product in products]

@app.get("/me", response_model=UserInfo)
def get_me(user: User = Depends(get_curent_user)):
    user.balance = user.wallet.balance
    return UserInfo.model_validate(user, from_attributes=True)
