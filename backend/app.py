from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import psycopg2
import psycopg2.extras
import os
from embedding import encode_text, encode_image, init_model

app = FastAPI(title="校园失物招领 API", version="1.0.0")


@app.on_event("startup")
def startup():
    init_model()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "lostfound"),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "password"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432")
}

def _vector_str(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def _build_vector(item_name: str, description: Optional[str] = None, image_url: Optional[str] = None) -> Optional[str]:
    text_parts = [item_name]
    if description:
        text_parts.append(description)
    text = " ".join(text_parts)
    try:
        if image_url and os.path.isfile(image_url):
            vec = encode_image(image_url)
        else:
            vec = encode_text(text)
        return _vector_str(vec)
    except Exception:
        return None


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

class UserCreate(BaseModel):
    student_id: str
    name: str
    phone: Optional[str] = None
    qq: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    student_id: str
    name: str
    phone: Optional[str] = None
    qq: Optional[str] = None
    email: Optional[str] = None
    role: str
    created_at: datetime

class LostItemCreate(BaseModel):
    item_name: str
    item_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    lost_time: Optional[str] = None
    status: Optional[str] = "lost"
    image_url: Optional[str] = None
    contact_person: str
    contact_phone: Optional[str] = None
    contact_qq: Optional[str] = None

class LostItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    found_time: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None

class LostItemResponse(BaseModel):
    id: int
    item_name: str
    item_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    lost_time: Optional[str] = None
    found_time: Optional[str] = None
    status: str
    image_url: Optional[str] = None
    contact_person: str
    contact_phone: Optional[str] = None
    contact_qq: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@app.get("/api/users", response_model=List[UserResponse])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(u) for u in users]

@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            "INSERT INTO users (student_id, name, phone, qq, email) VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (user.student_id, user.name, user.phone, user.qq, user.email)
        )
        conn.commit()
        new_user = cur.fetchone()
        return dict(new_user)
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="学号已存在")
    finally:
        cur.close()
        conn.close()

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return dict(user)

@app.get("/api/lost-items")
def get_lost_items(
    status: Optional[str] = None,
    item_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # 构建查询条件
    where_clause = "WHERE 1=1"
    params = []
    
    if status:
        where_clause += " AND status = %s"
        params.append(status)
    if item_type:
        where_clause += " AND item_type = %s"
        params.append(item_type)
    
    # 查询总数
    count_query = f"SELECT COUNT(*) as total FROM lost_items {where_clause}"
    cur.execute(count_query, params)
    total = cur.fetchone()['total']
    
    # 查询分页数据
    query = f"SELECT * FROM lost_items {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, (page - 1) * page_size])
    
    cur.execute(query, params)
    items = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        "items": [dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@app.post("/api/lost-items", response_model=LostItemResponse)
def create_lost_item(item: LostItemCreate):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    vector = _build_vector(item.item_name, item.description, item.image_url)
    try:
        cur.execute(
            """INSERT INTO lost_items
               (item_name, item_type, description, location, lost_time, status,
                image_url, contact_person, contact_phone, contact_qq, vector)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector) RETURNING *""",
            (item.item_name, item.item_type, item.description, item.location,
             item.lost_time, item.status, item.image_url, item.contact_person,
             item.contact_phone, item.contact_qq, vector)
        )
        conn.commit()
        new_item = cur.fetchone()
        return dict(new_item)
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="创建失物信息失败")
    finally:
        cur.close()
        conn.close()

@app.get("/api/lost-items/{item_id}", response_model=LostItemResponse)
def get_lost_item(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM lost_items WHERE id = %s", (item_id,))
    item = cur.fetchone()
    cur.close()
    conn.close()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    return dict(item)

@app.put("/api/lost-items/{item_id}", response_model=LostItemResponse)
def update_lost_item(item_id: int, item: LostItemUpdate):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        update_fields = []
        params = []
        
        if item.item_name:
            update_fields.append("item_name = %s")
            params.append(item.item_name)
        if item.item_type:
            update_fields.append("item_type = %s")
            params.append(item.item_type)
        if item.description:
            update_fields.append("description = %s")
            params.append(item.description)
        if item.location:
            update_fields.append("location = %s")
            params.append(item.location)
        if item.found_time:
            update_fields.append("found_time = %s")
            params.append(item.found_time)
        if item.status:
            update_fields.append("status = %s")
            params.append(item.status)
        if item.image_url:
            update_fields.append("image_url = %s")
            params.append(item.image_url)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="没有要更新的字段")

        if item.item_name or item.description or item.image_url:
            cur.execute("SELECT item_name, description, image_url FROM lost_items WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if row:
                new_name = item.item_name or row["item_name"]
                new_desc = item.description or row["description"]
                new_img = item.image_url or row["image_url"]
                vector = _build_vector(new_name, new_desc, new_img)
                update_fields.append("vector = %s::vector")
                params.append(vector)

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(item_id)
        
        query = "UPDATE lost_items SET " + ", ".join(update_fields) + " WHERE id = %s RETURNING *"
        cur.execute(query, params)
        conn.commit()
        updated_item = cur.fetchone()
        
        if not updated_item:
            raise HTTPException(status_code=404, detail="物品不存在")
        
        return dict(updated_item)
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="更新失物信息失败")
    finally:
        cur.close()
        conn.close()

@app.delete("/api/lost-items/{item_id}")
def delete_lost_item(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM lost_items WHERE id = %s", (item_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="物品不存在")
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="删除失物信息失败")
    finally:
        cur.close()
        conn.close()

@app.get("/api/search")
def search_lost_items(
    query: str = Query(..., min_length=1),
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    search_query = "SELECT * FROM lost_items WHERE 1=1"
    params = []
    
    if item_type:
        search_query += " AND item_type = %s"
        params.append(item_type)
    if status:
        search_query += " AND status = %s"
        params.append(status)
    
    search_query += " AND (item_name ILIKE %s OR description ILIKE %s OR location ILIKE %s)"
    params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    
    search_query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    cur.execute(search_query, params)
    items = cur.fetchall()
    cur.close()
    conn.close()
    
    return {"results": [dict(item) for item in items]}


@app.get("/api/semantic-search")
def semantic_search(
    query: str = Query(..., min_length=1),
    limit: int = 10
):
    try:
        vec = encode_text(query)
    except Exception:
        raise HTTPException(status_code=500, detail="向量模型未就绪")

    vector_str = _vector_str(vec)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(
            """SELECT *, 1 - (vector <=> %s::vector) AS similarity
               FROM lost_items
               WHERE vector IS NOT NULL
               ORDER BY vector <=> %s::vector
               LIMIT %s""",
            (vector_str, vector_str, limit)
        )
        items = cur.fetchall()
        return {"results": [dict(item) for item in items]}
    finally:
        cur.close()
        conn.close()


@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM lost_items WHERE status = 'lost'")
    lost_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM lost_items WHERE status = 'found'")
    found_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM lost_items")
    total_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return {
        "total_items": total_count,
        "lost_count": lost_count,
        "found_count": found_count,
        "user_count": user_count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)