from typing import Optional, List, Literal
from sqlmodel import SQLModel, Field, Relationship, Session, select
from enum import Enum
from pydantic import EmailStr
from schems.posts import CreateCartItem, CreateOrder, CreateUserOpen, CreateUser, CreateProduct, AuthUser
from fastapi import HTTPException


class Role(str, Enum):
    buyer = "buyer"
    seller = "seller"

class OrderStatus(str, Enum):
    created	= "created"
    acknowledged = "acknowledged"
    shipped = "shipped"
    received = "received"	
    confirmed = "confirmed"
    cancelled = "cancelled"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, nullable=False, unique=True)
    name: str = Field(max_length=128,index=True, nullable=False, unique=True)
    password_hash: str
    role: Role
    wallet: Optional["Wallet"] = Relationship(back_populates="user")
    cart_items: List["CartItem"] = Relationship(back_populates="buyer")
    products: List["Product"] = Relationship(back_populates="seller")
    seller_orders: List["Order"] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={"foreign_keys": "[Order.seller_id]"}
    )
    buyer_orders: List["Order"] = Relationship(
        back_populates="buyer",
        sa_relationship_kwargs={"foreign_keys": "[Order.buyer_id]"}
    )
    @classmethod
    def get_token(cls, db: Session, user: "AuthUser") -> str:
        from utils import verify_password, generate_token
        db_user = cls.get_by_email(db, user.email)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found.")
        if not verify_password(user.password, db_user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect password.")
        return generate_token(db_user.id)

    @classmethod
    def create_user(cls, db: Session, user: "CreateUserOpen"):
        if cls.get_by_email(db, user.email):
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists."
            )
        elif db.exec(select(cls).where(cls.name == user.name)).first():
            raise HTTPException(
                status_code=400,
                detail="User with this name already exists."
            )
        user_instance = User(**CreateUser.from_create_user_open(user).model_dump())

        db.add(user_instance)
        db.commit()
        db.refresh(user_instance)
        user_instance.create_wallet(db)
          
    def create_wallet(self, db: Session):
        db.add(Wallet(user_id=self.id))
        db.commit()
        db.refresh(self)

    @classmethod
    def get_by_email(cls, db: Session, email: EmailStr) -> Optional["User"]:
        return db.exec(select(cls).where(cls.email == email)).first()

    @classmethod
    def get_by_id(cls, db: Session, user_id: int) -> Optional["User"]:
        return db.get(cls, user_id)

    def freeze(self, db: Session, amount: float):
        if amount > self.wallet.balance:
            raise HTTPException(status_code=400, detail="Insufficient balance to freeze the amount.")
        self.wallet.frozen += amount
        self.wallet.balance -= amount
        db.add(self.wallet)
        db.commit()
        db.refresh(self.wallet)
    
    def unfreeze(self, db: Session, amount: float):
        if amount > self.wallet.frozen:
            raise ValueError("Insufficient frozen amount to unfreeze.")
        self.wallet.frozen -= amount
        self.wallet.balance += amount
        db.add(self.wallet)
        db.commit()
           
    def add_balance(self, db: Session, amount: float):
        if amount < 0:
            raise HTTPException(status_code=400, detail="Cannot add a negative balance.")
        self.wallet.balance += amount
        db.add(self.wallet)
        db.commit()
        
    def add_product(self, db: Session, product: "CreateProduct"):
        db.add(Product(**product.model_dump(), seller_id=self.id))
        db.commit()
    
    def add_cart_item(self, db: Session, cart_item: "CreateCartItem"):
        product = db.get(Product, cart_item.product_id)
        if not product or cart_item.quantity > product.stock:
            raise HTTPException(status_code=400, detail="Insufficient product stock.")
        db.add(CartItem(**cart_item.model_dump(), buyer_id=self.id))
        db.commit()
    
    def delete_cart_item(self, db: Session, cart_item_id: int):
        cart_item = db.get(CartItem, cart_item_id)
        if not cart_item or cart_item.buyer_id != self.id:
            raise HTTPException(status_code=404, detail="Cart item not found or does not belong to the user.")
        db.delete(cart_item)
        db.commit()

    def transaction(self, db: Session, amount: float, seller: "User"):
        self.wallet.frozen -= amount
        seller.wallet.balance += amount
        db.add(self.wallet)
        db.add(seller.wallet)
        db.commit()
        db.refresh(self.wallet)
        db.refresh(seller.wallet)

    def create_order(self, db: Session, order: "CreateOrder"):
        cart_item = db.get(CartItem, order.cart_item_id)
        if not cart_item or cart_item.buyer_id != self.id:
            raise HTTPException(status_code=400, detail="Cart item not found or does not belong to the user.")
        if cart_item.quantity > cart_item.product.stock:
            raise HTTPException(status_code=400, detail="Insufficient product stock.")

        total_price = cart_item.product.price * cart_item.quantity
        if self.wallet.balance < total_price:
            raise HTTPException(status_code=400, detail="Insufficient balance to create the order.")

        self.freeze(db, total_price)
        cart_item.product.reserve(db, cart_item.quantity)
        
        order_instance = Order(
            buyer_id=self.id,
            seller_id=cart_item.product.seller_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            total_price=total_price
        )
        db.add(order_instance)
        db.delete(cart_item)
        db.commit()
    
    def order_acknowledged(self, db: Session, order_id: int):
        order = db.get(Order, order_id)
        if not order or order.seller_id != self.id:
            raise HTTPException(status_code=404, detail="Order not found or does not belong to the user.")
        if order.status != OrderStatus.created:
            raise HTTPException(status_code=400, detail="Order cannot be acknowledged in its current state.")
        order.status = OrderStatus.acknowledged
        db.add(order) 
        db.commit()
    
    def order_shipped(self, db: Session, order_id: int):
        order = db.get(Order, order_id)
        if not order or order.seller_id != self.id:
            raise HTTPException(status_code=404, detail="Order not found or does not belong to the user.")
        if order.status != OrderStatus.acknowledged:
            raise HTTPException(status_code=400, detail="Order cannot be shipped in its current state.")
        order.status = OrderStatus.shipped
        db.add(order)
        db.commit()
    
    def order_received(self, db: Session, order_id: int):
        order = db.get(Order, order_id)
        if not order or order.buyer_id != self.id:
            raise HTTPException(status_code=404, detail="Order not found or does not belong to the user.")
        if order.status != OrderStatus.shipped:
            raise HTTPException(status_code=400, detail="Order cannot be received in its current state.")
        order.status = OrderStatus.received
        db.add(order)
        db.commit()
    
    def order_confirmed(self, db: Session, order_id: int):
        order = db.get(Order, order_id)
        if not order or order.buyer_id != self.id:
            raise HTTPException(status_code=404, detail="Order not found or does not belong to the user.")
        if order.status != OrderStatus.received:
            raise HTTPException(status_code=400, detail="Order cannot be confirmed in its current state.")
        order.status = OrderStatus.confirmed
        order.product.unreserve(db, order.quantity)
        self.transaction(db, order.total_price, order.seller)
        db.add(order)
        db.commit()

    def order_cancelled(self, db: Session, order_id: int):
        order = db.get(Order, order_id)
        if not order or order.buyer_id != self.id:
            raise HTTPException(status_code=404, detail="Order not found or does not belong to the user.")
        if order.status in [OrderStatus.confirmed, OrderStatus.cancelled]:
            raise HTTPException(status_code=400, detail="Order cannot be cancelled in its current state.")
        order.status = OrderStatus.cancelled
        order.product.unreserve(db, order.quantity)
        self.unfreeze(db, order.total_price)
        db.add(order)
        db.commit()


class Wallet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    balance: float = Field(default=0.0, nullable=False)
    frozen: float = Field(default=0.0, nullable=False)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="wallet")
    
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    seller_id: int = Field(foreign_key="user.id")
    seller: User = Relationship(back_populates="products")
    orders: List["Order"] = Relationship(back_populates="product")
    cart_items: List["CartItem"] = Relationship(back_populates="product")
    name: str
    description: Optional[str]
    price: float
    stock: int
    reserved: int = Field(default=0)

    def reserve(self, db: Session, quantity: int):
        if quantity > self.stock:
            raise ValueError("Insufficient product stock.")
        self.reserved += quantity
        self.stock -= quantity
        db.add(self)
        db.commit()
    
    def unreserve(self, db: Session, quantity: int):
        if quantity > self.reserved:
            raise ValueError("Insufficient reserved stock to unreserve.")
        self.reserved -= quantity
        db.add(self)
        db.commit()

class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_id: int = Field(foreign_key="user.id")
    buyer: User = Relationship(back_populates="cart_items")
    product_id: int = Field(foreign_key="product.id")
    product: Product = Relationship(back_populates="cart_items")
    quantity: int

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_id: int = Field(foreign_key="user.id")
    buyer: User = Relationship(
        back_populates="buyer_orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.buyer_id]"}
    )
    seller_id: int = Field(foreign_key="user.id")
    seller: User = Relationship(
        back_populates="seller_orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.seller_id]"}
    )
    product_id: int = Field(foreign_key="product.id")
    product: Product = Relationship(back_populates="orders")
    quantity: int
    total_price: float
    status: OrderStatus = Field(default=OrderStatus.created)
    



    

