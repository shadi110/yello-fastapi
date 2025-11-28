from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json
import os
import time
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# --------------------------
# Database connection
# --------------------------
def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL environment variable is not set")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = psycopg.connect(database_url, sslmode='require')
            return conn
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Connection attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(5)
            else:
                raise e

# --------------------------
# Table creation
# --------------------------
def create_tables():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            profile_image TEXT,
            location TEXT,
            mobiles JSONB,
            reaching_video TEXT,
            social JSONB,
            type JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database table 'entries' is ready")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

# --------------------------
# Pydantic models
# --------------------------
class SocialModel(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    snapchat: Optional[str] = None
    telegram: Optional[str] = None
    tiktok: Optional[str] = None

class TypeModel(BaseModel):
    main: Optional[str] = None
    sub: Optional[str] = None

class EntryBase(BaseModel):
    title: str
    description: Optional[str] = None
    profile_image: Optional[str] = None
    location: Optional[str] = None
    mobiles: Optional[List[str]] = []  # Accept list of strings
    reaching_video: Optional[str] = None
    social: Optional[SocialModel] = SocialModel()
    type: Optional[TypeModel] = TypeModel()

class EntryCreate(EntryBase):
    pass

class EntryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    profile_image: Optional[str] = None
    location: Optional[str] = None
    mobiles: Optional[List[str]] = None
    reaching_video: Optional[str] = None
    social: Optional[SocialModel] = None
    type: Optional[TypeModel] = None

class EntryResponse(EntryBase):
    id: int
    created_at: str
    updated_at: str

# --------------------------
# Lifespan context manager
# --------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting FastAPI application...")
    create_tables()
    yield
    print("👋 Shutting down FastAPI application...")

# --------------------------
# FastAPI app
# --------------------------
app = FastAPI(
    title="Entries API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Entries API is running"}

# --------------------------
# CRUD Endpoints
# --------------------------
@app.post("/entries", response_model=EntryResponse)
async def create_entry(entry: EntryCreate):
    logger.debug("🚀 POST /entries called")
    logger.debug(f"Payload received: {entry.dict()}")

    try:
        conn = get_db_connection()
        logger.debug("✅ Database connection established")

        cur = conn.cursor(row_factory=dict_row)
        logger.debug("✅ Cursor created")

        # Prepare values
        values = (
            entry.title,
            entry.description,
            entry.profile_image,
            entry.location,
            Json(entry.mobiles),  # list as JSONB
            entry.reaching_video,
            Json(entry.social.dict() if entry.social else {}),  # dict as JSONB
            Json(entry.type.dict() if entry.type else {})       # dict as JSONB
        )
        logger.debug("DEBUG: Prepared values for insertion:")
        for name, val in zip(
            ["title","description","profile_image","location","mobiles","reaching_video","social","type"],
            values
        ):
            logger.debug(f"{name}={val}")

        cur.execute("""
            INSERT INTO entries
            (title, description, profile_image, location, mobiles, reaching_video, social, type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, values)

        new_entry = cur.fetchone()
        conn.commit()
        logger.debug(f"✅ Entry inserted with ID {new_entry['id']}")

        new_entry['created_at'] = new_entry['created_at'].isoformat()
        new_entry['updated_at'] = new_entry['updated_at'].isoformat()

        return new_entry

    except Exception as e:
        logger.error(f"❌ Error inserting entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        logger.debug("✅ Database connection closed")

# READ all
@app.get("/entries", response_model=List[EntryResponse])
async def get_all_entries(
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: Optional[int] = Query(0, ge=0)
):
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)

    cur.execute("SELECT * FROM entries ORDER BY id DESC LIMIT %s OFFSET %s", (limit, offset))
    entries = cur.fetchall()

    cur.close()
    conn.close()

    for entry in entries:
        entry['created_at'] = entry['created_at'].isoformat()
        entry['updated_at'] = entry['updated_at'].isoformat()
    return entries

# READ one
@app.get("/entries/{entry_id}", response_model=EntryResponse)
async def get_entry(entry_id: int):
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)

    cur.execute("SELECT * FROM entries WHERE id = %s", (entry_id,))
    entry = cur.fetchone()

    cur.close()
    conn.close()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry['created_at'] = entry['created_at'].isoformat()
    entry['updated_at'] = entry['updated_at'].isoformat()
    return entry

# UPDATE
@app.put("/entries/{entry_id}", response_model=EntryResponse)
async def update_entry(entry_id: int, new_data: EntryUpdate):
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)

    fields = {k: v for k, v in new_data.dict(exclude_unset=True).items()}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = %s" for k in fields.keys())
    values = []
    for k, v in fields.items():
        if k in ['social', 'type']:
            values.append(v.dict() if v else {})
        else:
            values.append(v)
    values.append(entry_id)

    cur.execute(f"UPDATE entries SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *", values)
    updated_entry = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not updated_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    updated_entry['created_at'] = updated_entry['created_at'].isoformat()
    updated_entry['updated_at'] = updated_entry['updated_at'].isoformat()
    return updated_entry

# DELETE
@app.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM entries WHERE id = %s RETURNING id", (entry_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": "Entry deleted successfully"}
