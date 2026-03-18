from fastapi import FastAPI, Query
from typing import Optional
import math

app = FastAPI(title="FastAPI Assignment 5 - Search, Sort & Pagination")

# ============================================================
# IN-MEMORY DATA
# ============================================================

# Pre-loaded products (from main_day6.py)
products = [
    {"product_id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics"},
    {"product_id": 2, "name": "Notebook", "price": 99, "category": "Stationery"},
    {"product_id": 3, "name": "USB Hub", "price": 799, "category": "Electronics"},
    {"product_id": 4, "name": "Pen Set", "price": 49, "category": "Stationery"},
]

# Orders list (starts empty, we add via POST)
orders = []
order_counter = 0


# ============================================================
# Q1 - SEARCH PRODUCTS (already built in day6)
# ============================================================
@app.get("/products/search")
def search_products(keyword: str = Query(..., description="Search keyword")):
    """
    Search products by keyword (case-insensitive).
    Returns matching products or a friendly message if none found.
    """
    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not results:
        return {
            "keyword": keyword,
            "total_found": 0,
            "message": f"No products found for: {keyword}"
        }

    return {
        "keyword": keyword,
        "total_found": len(results),
        "products": results
    }


# ============================================================
# Q2 - SORT PRODUCTS (already built in day6)
# ============================================================
@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price", description="Sort by 'price' or 'name'"),
    order: str = Query("asc", description="Order: 'asc' or 'desc'")
):
    """
    Sort products by price or name, ascending or descending.
    """
    # Validate sort_by
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    # Validate order
    if order not in ["asc", "desc"]:
        return {"error": "order must be 'asc' or 'desc'"}

    reverse = True if order == "desc" else False
    sorted_products = sorted(products, key=lambda x: x[sort_by], reverse=reverse)

    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_products
    }


# ============================================================
# Q3 - PAGINATE PRODUCTS (already built in day6)
# ============================================================
@app.get("/products/page")
def paginate_products(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(2, ge=1, description="Products per page")
):
    """
    Paginate through products list.
    """
    total_products = len(products)
    total_pages = math.ceil(total_products / limit)

    start = (page - 1) * limit
    end = start + limit
    page_products = products[start:end]

    return {
        "page": page,
        "limit": limit,
        "total_products": total_products,
        "total_pages": total_pages,
        "products": page_products
    }


# ============================================================
# Q4 - SEARCH ORDERS BY CUSTOMER NAME (new code)
# ============================================================
@app.get("/orders/search")
def search_orders(
    customer_name: str = Query(..., description="Customer name to search")
):
    """
    Search orders by customer name (case-insensitive partial match).
    """
    results = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]

    if not results:
        return {
            "customer_name": customer_name,
            "total_found": 0,
            "message": f"No orders found for customer: {customer_name}"
        }

    return {
        "customer_name": customer_name,
        "total_found": len(results),
        "orders": results
    }


# ============================================================
# Q5 - SORT PRODUCTS BY CATEGORY THEN PRICE (new code)
# ============================================================
@app.get("/products/sort-by-category")
def sort_by_category():
    """
    Sort products by category alphabetically (A→Z),
    then by price ascending within each category.
    """
    sorted_products = sorted(products, key=lambda x: (x["category"], x["price"]))

    # Group them for clear display
    grouped = {}
    for p in sorted_products:
        cat = p["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(p)

    return {
        "total_products": len(sorted_products),
        "sorted_products": sorted_products,
        "grouped_by_category": grouped
    }


# ============================================================
# Q6 - BROWSE: SEARCH + SORT + PAGINATE COMBINED (new code)
# ============================================================
@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = Query(None, description="Search keyword (optional)"),
    sort_by: str = Query("price", description="Sort by 'price' or 'name'"),
    order: str = Query("asc", description="Order: 'asc' or 'desc'"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(4, ge=1, description="Products per page")
):
    """
    Combined endpoint: Search → Sort → Paginate.
    All parameters are optional with sensible defaults.
    """
    # Validate sort_by
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    # Validate order
    if order not in ["asc", "desc"]:
        return {"error": "order must be 'asc' or 'desc'"}

    # Step 1: FILTER by keyword (if provided)
    if keyword:
        filtered = [
            p for p in products
            if keyword.lower() in p["name"].lower()
        ]
    else:
        filtered = products.copy()

    # Step 2: SORT the filtered results
    reverse = True if order == "desc" else False
    sorted_results = sorted(filtered, key=lambda x: x[sort_by], reverse=reverse)

    # Step 3: PAGINATE the sorted results
    total_found = len(sorted_results)
    total_pages = math.ceil(total_found / limit) if total_found > 0 else 0

    start = (page - 1) * limit
    end = start + limit
    page_products = sorted_results[start:end]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total_found,
        "total_pages": total_pages,
        "products": page_products
    }


# ============================================================
# BONUS - PAGINATE ORDERS
# ============================================================
@app.get("/orders/page")
def paginate_orders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(3, ge=1, description="Orders per page")
):
    """
    Paginate through orders list.
    """
    total_orders = len(orders)
    total_pages = math.ceil(total_orders / limit) if total_orders > 0 else 0

    start = (page - 1) * limit
    end = start + limit
    page_orders = orders[start:end]

    return {
        "page": page,
        "limit": limit,
        "total_orders": total_orders,
        "total_pages": total_pages,
        "orders": page_orders
    }


# ============================================================
# GET SINGLE PRODUCT BY ID (must be LAST — dynamic route)
# ============================================================
@app.get("/products/{product_id}")
def get_product(product_id: int):
    """Get a single product by its ID."""
    for p in products:
        if p["product_id"] == product_id:
            return p
    return {"error": f"Product with id {product_id} not found"}


# ============================================================
# POST - CREATE ORDER (needed for Q4 and Bonus testing)
# ============================================================
@app.post("/orders")
def create_order(
    customer_name: str = Query(..., description="Customer name"),
    product_id: int = Query(..., description="Product ID"),
    quantity: int = Query(1, ge=1, description="Quantity")
):
    """
    Place a new order.
    """
    global order_counter

    # Find product
    product = None
    for p in products:
        if p["product_id"] == product_id:
            product = p
            break

    if not product:
        return {"error": f"Product with id {product_id} not found"}

    order_counter += 1
    total_price = product["price"] * quantity

    new_order = {
        "order_id": order_counter,
        "customer_name": customer_name,
        "product_name": product["name"],
        "product_id": product_id,
        "quantity": quantity,
        "total_price": total_price
    }

    orders.append(new_order)
    return {"message": "Order placed successfully", "order": new_order}