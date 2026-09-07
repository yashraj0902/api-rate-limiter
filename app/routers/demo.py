from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/demo", tags=["Demo Endpoints"])

class Order(BaseModel):
    id: int
    item: str
    quantity: int

class Product(BaseModel):
    id: int
    name: str
    price: float

@router.get("/orders", response_model=List[Order], summary="Get demo orders")
async def get_orders():
    """Returns a mock list of orders. Subject to rate limiting."""
    return [
        Order(id=1, item="Laptop", quantity=1),
        Order(id=2, item="Mouse", quantity=2)
    ]

@router.post("/orders", response_model=Order, summary="Create a demo order")
async def create_order():
    """Creates a mock order. Subject to rate limiting."""
    return Order(id=3, item="Keyboard", quantity=1)

@router.get("/products", response_model=List[Product], summary="Get demo products")
async def get_products():
    """Returns a mock list of products. Subject to rate limiting."""
    return [
        Product(id=101, name="Monitor", price=199.99),
        Product(id=102, name="Desk", price=299.99)
    ]
