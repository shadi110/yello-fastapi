from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import engine, SessionLocal, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# CREATE
@app.post("/entries", response_model=schemas.Entry)
def create_entry(entry: schemas.EntryCreate, db: Session = Depends(get_db)):
    db_entry = models.Entry(
        title=entry.title,
        description=entry.description,
        profile_image=entry.profile_image,
        location=entry.location,
        mobiles=entry.mobiles,
        reaching_video=entry.reaching_video,
        social=entry.social.dict(),
        type=entry.type.dict(),
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


# READ all
@app.get("/entries", response_model=List[schemas.Entry])
def get_all_entries(db: Session = Depends(get_db)):
    return db.query(models.Entry).all()


# READ one
@app.get("/entries/{entry_id}", response_model=schemas.Entry)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


# UPDATE
@app.put("/entries/{entry_id}", response_model=schemas.Entry)
def update_entry(entry_id: int, new_data: schemas.EntryUpdate, db: Session = Depends(get_db)):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    for key, value in new_data.dict().items():
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return entry


# DELETE
@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()
    return {"message": "Entry deleted successfully"}
