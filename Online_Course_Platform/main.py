from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(title="Online Courses Platform", description="API for managing online courses and enrollments", version="1.0.0")

# -----------------------
# DATA
# -----------------------

courses = [
    {"id": 1, "title": "FastAPI Basics", "instructor": "Alice", "category": "Web Dev", "level": "Beginner", "price": 0, "seats_left": 10},
    {"id": 2, "title": "React Mastery", "instructor": "Bob", "category": "Web Dev", "level": "Intermediate", "price": 3000, "seats_left": 5},
    {"id": 3, "title": "Data Science 101", "instructor": "Charlie", "category": "Data Science", "level": "Beginner", "price": 2500, "seats_left": 8},
    {"id": 4, "title": "UI/UX Design", "instructor": "Diana", "category": "Design", "level": "Beginner", "price": 2000, "seats_left": 6},
    {"id": 5, "title": "Docker & DevOps", "instructor": "Evan", "category": "DevOps", "level": "Advanced", "price": 4000, "seats_left": 3},
    {"id": 6, "title": "ML Advanced", "instructor": "Frank", "category": "Data Science", "level": "Advanced", "price": 5000, "seats_left": 2},
]

enrollments = []
enrollment_counter = 1

wishlist = []

# -----------------------
# MODELS
# -----------------------

class EnrollRequest(BaseModel):
    student_name: str = Field(..., min_length=2)
    course_id: int = Field(..., gt=0)
    email: str = Field(..., min_length=5)
    payment_method: str = "card"
    coupon_code: str = ""
    gift_enrollment: bool = False
    recipient_name: str = ""


class NewCourse(BaseModel):
    title: str = Field(..., min_length=2)
    instructor: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    level: str = Field(..., min_length=2)
    price: int = Field(..., ge=0)
    seats_left: int = Field(..., gt=0)


class WishlistEnrollRequest(BaseModel):
    student_name: str
    payment_method: str = "card"


# -----------------------
# HELPERS
# -----------------------

def find_course(course_id):
    return next((c for c in courses if c["id"] == course_id), None)


def calculate_enrollment_fee(price, seats_left, coupon_code):
    final_price = price
    discounts = []

    if seats_left > 5:
        discount = final_price * 0.10
        final_price -= discount
        discounts.append("10% early-bird")

    if coupon_code == "STUDENT20":
        discount = final_price * 0.20
        final_price -= discount
        discounts.append("20% coupon")
    elif coupon_code == "FLAT500":
        final_price -= 500
        discounts.append("₹500 off")

    return max(final_price, 0), discounts


def filter_courses_logic(data, category, level, max_price, has_seats):
    result = data

    if category is not None:
        result = [c for c in result if c["category"] == category]

    if level is not None:
        result = [c for c in result if c["level"] == level]

    if max_price is not None:
        result = [c for c in result if c["price"] <= max_price]

    if has_seats:
        result = [c for c in result if c["seats_left"] > 0]

    return result


# -----------------------
# ROOT
# -----------------------

@app.get("/")
def home():
    return {"message": "Welcome to LearnHub Online Courses"}


# -----------------------
# COURSES
# -----------------------

@app.get("/courses")
def get_courses():
    return {
        "courses": courses,
        "total": len(courses),
        "total_seats_available": sum(c["seats_left"] for c in courses)
    }


@app.get("/courses/summary")
def courses_summary():
    return {
        "total_courses": len(courses),
        "free_courses": len([c for c in courses if c["price"] == 0]),
        "most_expensive": max(courses, key=lambda x: x["price"]),
        "total_seats": sum(c["seats_left"] for c in courses),
        "category_count": {cat: sum(1 for c in courses if c["category"] == cat)
                           for cat in set(c["category"] for c in courses)}
    }





@app.post("/courses", status_code=201)
def create_course(data: NewCourse):
    if any(c["title"] == data.title for c in courses):
        raise HTTPException(400, "Duplicate course title")

    new_course = data.dict()
    new_course["id"] = max(c["id"] for c in courses) + 1

    courses.append(new_course)
    return new_course




# -----------------------
# ENROLLMENTS
# -----------------------

@app.get("/enrollments")
def get_enrollments():
    return {"enrollments": enrollments, "total": len(enrollments)}


@app.post("/enrollments")
def enroll(data: EnrollRequest):
    global enrollment_counter

    course = find_course(data.course_id)
    if not course:
        raise HTTPException(404, "Course not found")

    if course["seats_left"] <= 0:
        raise HTTPException(400, "No seats available")

    if data.gift_enrollment and not data.recipient_name:
        raise HTTPException(400, "Recipient required for gift")

    final_fee, discounts = calculate_enrollment_fee(
        course["price"], course["seats_left"], data.coupon_code
    )

    course["seats_left"] -= 1

    enrollment = {
        "enrollment_id": enrollment_counter,
        "student_name": data.student_name,
        "course_title": course["title"],
        "instructor": course["instructor"],
        "original_price": course["price"],
        "final_fee": final_fee,
        "discounts": discounts,
        "recipient": data.recipient_name if data.gift_enrollment else None
    }

    enrollments.append(enrollment)
    enrollment_counter += 1

    return enrollment


@app.get("/enrollments/search")
def search_enrollments(student_name: str):
    result = [e for e in enrollments if student_name.lower() in e["student_name"].lower()]
    return {"results": result, "total": len(result)}


@app.get("/enrollments/sort")
def sort_enrollments(order: str = "asc"):
    reverse = order == "desc"
    return sorted(enrollments, key=lambda x: x["final_fee"], reverse=reverse)


@app.get("/enrollments/page")
def paginate_enrollments(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit
    return enrollments[start:end]


# -----------------------
# WISHLIST
# -----------------------

@app.post("/wishlist/add")
def add_wishlist(student_name: str, course_id: int):
    if not find_course(course_id):
        raise HTTPException(404, "Course not found")

    if any(w["student_name"] == student_name and w["course_id"] == course_id for w in wishlist):
        raise HTTPException(400, "Already in wishlist")

    wishlist.append({"student_name": student_name, "course_id": course_id})
    return {"message": "Added to wishlist"}


@app.get("/wishlist")
def get_wishlist():
    total_value = sum(find_course(w["course_id"])["price"] for w in wishlist)
    return {"wishlist": wishlist, "total_value": total_value}




@app.post("/wishlist/enroll-all")
def enroll_all(data: WishlistEnrollRequest):
    results = []
    total_fee = 0

    student_items = [w for w in wishlist if w["student_name"] == data.student_name]

    for item in student_items:
        course = find_course(item["course_id"])

        if course and course["seats_left"] > 0:
            fee, _ = calculate_enrollment_fee(course["price"], course["seats_left"], "")

            course["seats_left"] -= 1
            total_fee += fee

            results.append({
                "course": course["title"],
                "fee": fee
            })

            wishlist.remove(item)

    return {
        "enrolled": len(results),
        "total_fee": total_fee,
        "details": results
    }


# -----------------------
# SEARCH / FILTER / SORT / PAGINATION
# -----------------------

@app.get("/courses/filter")
def filter_courses(category: str = None, level: str = None,
                   max_price: int = None, has_seats: bool = None):
    result = filter_courses_logic(courses, category, level, max_price, has_seats)
    return {"results": result, "total": len(result)}


@app.get("/courses/search")
def search_courses(keyword: str):
    result = [
        c for c in courses
        if keyword.lower() in c["title"].lower()
        or keyword.lower() in c["instructor"].lower()
        or keyword.lower() in c["category"].lower()
    ]
    return {"results": result, "total_found": len(result)}


@app.get("/courses/sort")
def sort_courses(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "title", "seats_left"]:
        raise HTTPException(400, "Invalid sort field")

    reverse = order == "desc"
    return sorted(courses, key=lambda x: x[sort_by], reverse=reverse)


@app.get("/courses/page")
def paginate_courses(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit
    total_pages = (len(courses) + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "data": courses[start:end]
    }


@app.get("/courses/browse")
def browse_courses(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    max_price: Optional[int] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    result = courses

    # 1. keyword
    if keyword:
        result = [
            c for c in result
            if keyword.lower() in c["title"].lower()
            or keyword.lower() in c["instructor"].lower()
            or keyword.lower() in c["category"].lower()
        ]

    # 2–4 filters
    result = filter_courses_logic(result, category, level, max_price, None)

    # 5 sorting
    reverse = order == "desc"
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    # 6 pagination
    start = (page - 1) * limit
    end = start + limit
    total_pages = (len(result) + limit - 1) // limit

    return {
        "total_results": len(result),
        "page": page,
        "total_pages": total_pages,
        "results": result[start:end]
    }


@app.get("/courses/{course_id}")
def get_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    return course

@app.put("/courses/{course_id}")
def update_course(course_id: int, price: Optional[int] = None, seats_left: Optional[int] = None):
    course = find_course(course_id)
    if not course:
        raise HTTPException(404, "Course not found")

    if price is not None:
        course["price"] = price
    if seats_left is not None:
        course["seats_left"] = seats_left

    return course


@app.delete("/courses/{course_id}")
def delete_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(404, "Course not found")

    if any(e["course_title"] == course["title"] for e in enrollments):
        raise HTTPException(400, "Cannot delete course with enrollments")

    courses.remove(course)
    return {"message": "Course deleted"}

@app.delete("/wishlist/remove/{course_id}")
def remove_wishlist(course_id: int, student_name: str):
    for w in wishlist:
        if w["course_id"] == course_id and w["student_name"] == student_name:
            wishlist.remove(w)
            return {"message": "Removed"}
    raise HTTPException(404, "Item not found")
