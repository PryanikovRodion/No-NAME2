from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from schems.posts import CreateUserOpen, AuthUser, Token, ProductInfo, UserInfo
from database.db import get_session
from database.models import User, Product
from sqlmodel import Session, select
from utils import get_curent_user

app = APIRouter()

@app.post("/registration")
def registration(user: CreateUserOpen, db: Session = Depends(get_session)):
    User.create_user(db, user)
    return {"message": "User created successfully"}

@app.post("/token", response_model=Token)
def login(auth_user: AuthUser, db: Session = Depends(get_session)):
    return Token(access_token=User.get_token(db, auth_user))

@app.get("/product/{product_id}", response_model=ProductInfo)
def get_product(product_id: int, db: Session = Depends(get_session)):
    product = ProductInfo.model_validate(db.get(Product, product_id), from_attributes=True)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/products", response_model=list[ProductInfo])
def get_products(db: Session = Depends(get_session)):
    products = db.exec(select(Product)).all()
    return [ProductInfo.model_validate(product, from_attributes=True) for product in products]

@app.get("/me", response_model=UserInfo)
def get_me(user: User = Depends(get_curent_user)):
    return UserInfo.model_validate(user, from_attributes=True)
