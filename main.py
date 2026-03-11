from fastapi import FastAPI
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

app = FastAPI()

# --- Unified Product Data ---
products = [
    {"id": 1, "name": "Laptop", "price": 55000, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 50, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Pen", "price": 10, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "Mouse", "price": 500, "category": "Electronics", "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False},
]

feedback = []
orders = []
order_counter = 0

# --- Basic Store Endpoints ---
@app.get("/")
def home():
    return {"message": "FastAPI running"}

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    result = [p for p in products if p["category"].lower() == category_name.lower()]
    if not result:
        return {"error": "No products found in this category"}
    return {"category": category_name, "products": result, "total": len(result)}

@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"]]
    return {"in_stock_products": available, "count": len(available)}

@app.get("/store/summary")
def store_summary():
    in_stock_count = len([p for p in products if p["in_stock"]])
    out_stock_count = len(products) - in_stock_count
    categories = list(set([p["category"] for p in products]))
    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories
    }

@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    results = [p for p in products if keyword.lower() in p["name"].lower()]
    if not results:
        return {"message": "No products matched your search"}
    return {"keyword": keyword, "results": results, "total_matches": len(results)}

@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    return {"best_deal": cheapest, "premium_pick": expensive}

# --- Assignment Tasks ---
@app.get("/products/filter")
def filter_products(category: Optional[str] = None,
                    min_price: Optional[int] = None,
                    max_price: Optional[int] = None):
    result = products
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    return result

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}
    return {"error": "Product not found"}

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

@app.post("/feedback")
def submit_feedback(fb: CustomerFeedback):
    feedback.append(fb.dict())
    return {
        "message": "Feedback submitted successfully",
        "feedback": fb.dict(),
        "total_feedback": len(feedback)
    }

@app.get("/products/summary")
def product_summary():
    total = len(products)
    in_stock = sum(1 for p in products if p["in_stock"])
    out_stock = total - in_stock
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    categories = list({p["category"] for p in products})
    return {
        "total_products": total,
        "in_stock_count": in_stock,
        "out_of_stock_count": out_stock,
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: EmailStr
    items: List[OrderItem] = Field(..., min_items=1)

@app.post("/orders/bulk")
def bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
            continue
        if not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
            continue
        subtotal = product["price"] * item.quantity
        confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})
        grand_total += subtotal
    return {"company": order.company_name, "confirmed": confirmed, "failed": failed, "grand_total": grand_total}

class SimpleOrder(BaseModel):
    product_id: int
    quantity: int

@app.post("/orders")
def place_order(order: SimpleOrder):
    global order_counter
    product = next((p for p in products if p["id"] == order.product_id), None)
    if not product:
        return {"error": "Product not found"}
    order_counter += 1
    new_order = {
        "id": order_counter,
        "product": product["name"],
        "quantity": order.quantity,
        "status": "pending"
    }
    orders.append(new_order)
    return new_order

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    return order

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    order["status"] = "confirmed"
    return order