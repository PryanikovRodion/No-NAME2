from pydantic import BaseModel, EmailStr, Field, conint
from typing import Optional, List
from enum import Enum
from utils import hash_password

class Role(str, Enum):
    buyer = "buyer"
    seller = "seller"

class OrderStatus(str, Enum):
    created = "created"
    acknowledged = "acknowledged"
    shipped = "shipped"
    received = "received"
    confirmed = "confirmed"
    cancelled = "cancelled"

class CreateCartItem(BaseModel):
    product_id: int = Field(..., ge=1, example=2)
    quantity: int = Field(..., ge=1, example=2)
    class Config:
        extra = "ignore"

class CreateOrder(BaseModel):
    cart_item_id: int = Field(..., ge=1, example=2)
    class Config:
        extra = "ignore"

class CreateUserOpen(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    name: str = Field(..., max_length=128, example="John Doe")
    password: str = Field(..., min_length=8, example="password")
    role: Role = Field(..., example=Role.buyer)

class CreateUser(CreateUserOpen):
    email: EmailStr = Field(..., example="user@example.com")
    name: str = Field(..., max_length=128, example="John Doe")
    password_hash: str = Field(..., example="password")
    role: Role = Field(..., example=Role.buyer)

    @classmethod
    def from_create_user_open(cls, user_open: CreateUserOpen) -> "CreateUser":
        return cls(
            email=user_open.email,
            name=user_open.name,
            password_hash=hash_password(user_open.password),
            role=user_open.role
        )

class CreateProduct(BaseModel):
    name: str = Field(..., max_length=128, example="Product Name")
    description: Optional[str] = Field(None, max_length=512, example="Product Description")
    price: float = Field(..., gt=0, example=19.99)
    stock: int = Field(..., ge=0, example=100)
  
    class Config:
        extra = "ignore"

class AuthUser(BaseModel):
    email: EmailStr = Field(..., example="helloworld@gmail.com")
    password: str = Field(..., min_length=8, example="password")

class Token(BaseModel):
    access_token: str = Field(..., example="access_token")

class ProductInfo(BaseModel):
    id: int = Field(..., ge=1, example=1)
    name: str = Field(..., max_length=128, example="Product Name")
    description: Optional[str] = Field(None, max_length=512, example="Product Description")
    price: float = Field(..., gt=0, example=19.99)
    stock: int = Field(..., ge=0, example=100)
    class Config:
        extra = "ignore"

class UserInfo(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    name: str = Field(..., max_length=128, example="John Doe")
    role: Role = Field(..., example=Role.buyer)
    balance: float = Field(..., ge=0, example=0)
    class Config:
        extra = "ignore"

class CartItemsInfo(BaseModel):
    id: int = Field(..., ge=1, example=1)
    product_id: int = Field(..., ge=1, example=2)
    quantity: int = Field(..., ge=1, example=2)
    product: ProductInfo
    class Config:
        extra = "ignore"

class OrderInfo(BaseModel):
    id: int = Field(..., ge=1, example=1)
    status: OrderStatus = Field(..., example=OrderStatus.created)
    quantity: int = Field(..., ge=1, example=2)
    product: ProductInfo
    total_price: float = Field(..., gt=0, example=39.98)
    class Config:
        extra = "ignore"

class OrderFullInfo(OrderInfo):
    id: int = Field(..., ge=1, example=1)
    status: OrderStatus = Field(..., example=OrderStatus.created)
    quantity: int = Field(..., ge=1, example=2)
    product: ProductInfo
    total_price: float = Field(..., gt=0, example=39.98)
    class Config:
        extra = "ignore"

class ProductFullInfo(BaseModel):
    id: int = Field(..., ge=1, example=1)
    name: str = Field(..., max_length=128, example="Product Name")
    description: Optional[str] = Field(None, max_length=512, example="Product Description")
    price: float = Field(..., gt=0, example=19.99)
    stock: int = Field(..., ge=0, example=100)
    reserved: int = Field(..., ge=0, example=22)
    orders: List[OrderFullInfo]
    class Config:
        extra = "ignore"
