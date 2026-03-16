from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Cart System - Day 5 Practice")

# PRODUCT CATALOG
products = {
    1: {"product_id": 1, "product_name": "Wireless Mouse", "price": 499, "in_stock": True},
    2: {"product_id": 2, "product_name": "Notebook", "price": 99, "in_stock": True},
    3: {"product_id": 3, "product_name": "USB Hub", "price": 299, "in_stock": False},
    4: {"product_id": 4, "product_name": "Pen Set", "price": 49, "in_stock": True},
}

# IN-MEMORY CART AND ORDERS

cart = {}       # key = product_id, value = {"product_id", "product_name", "quantity", "unit_price", "subtotal"}
orders = []     # list of placed orders
order_counter = 0  # auto-increment order id

# PYDANTIC MODEL FOR CHECKOUT

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

# ENDPOINT: GET /products — View all products

@app.get("/products")
def get_products():
    return {"products": list(products.values()), "total_products": len(products)}

# ENDPOINT: POST /cart/add — Add item to cart

@app.post("/cart/add")
def add_to_cart(product_id: int = Query(...), quantity: int = Query(default=1)):
    # Check if product exists
    if product_id not in products:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    product = products[product_id]

    # Check if product is in stock
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['product_name']} is out of stock")

    # Check if quantity is valid
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    # If product already in cart, UPDATE quantity
    if product_id in cart:
        cart[product_id]["quantity"] += quantity
        cart[product_id]["subtotal"] = cart[product_id]["quantity"] * cart[product_id]["unit_price"]
        return {
            "message": "Cart updated",
            "cart_item": cart[product_id]
        }

    # Otherwise, ADD new item to cart
    cart_item = {
        "product_id": product_id,
        "product_name": product["product_name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": product["price"] * quantity
    }
    cart[product_id] = cart_item

    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }

# ENDPOINT: GET /cart — View cart

@app.get("/cart")
def view_cart():
    if not cart:
        return {"message": "Cart is empty", "items": [], "item_count": 0, "grand_total": 0}

    items = list(cart.values())
    grand_total = sum(item["subtotal"] for item in items)

    return {
        "items": items,
        "item_count": len(items),
        "grand_total": grand_total
    }

# ENDPOINT: DELETE /cart/{product_id} — Remove item from cart

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    if product_id not in cart:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} is not in the cart")

    removed_item = cart.pop(product_id)

    return {
        "message": f"{removed_item['product_name']} removed from cart",
        "removed_item": removed_item
    }

# ENDPOINT: POST /cart/checkout — Checkout

@app.post("/cart/checkout")
def checkout(request: CheckoutRequest):
    global order_counter

    # Check if cart is empty
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty. Add items before checkout.")

    orders_placed = []
    grand_total = 0

    for item in cart.values():
        order_counter += 1
        order = {
            "order_id": order_counter,
            "customer_name": request.customer_name,
            "delivery_address": request.delivery_address,
            "product": item["product_name"],
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "subtotal": item["subtotal"]
        }
        orders.append(order)
        orders_placed.append(order)
        grand_total += item["subtotal"]

    # Clear the cart after checkout
    cart.clear()

    return {
        "message": "Checkout successful",
        "orders_placed": orders_placed,
        "total_items_ordered": len(orders_placed),
        "grand_total": grand_total
    }

# ENDPOINT: GET /orders — View all orders

@app.get("/orders")
def get_orders():
    if not orders:
        return {"message": "No orders yet", "orders": [], "total_orders": 0}

    return {
        "orders": orders,
        "total_orders": len(orders)
    }