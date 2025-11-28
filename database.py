from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://yell_db_user:ax0gHANYc29tJEzbxBIqan0x0cujQ1AY@dpg-d4ks8lre5dus73febmlg-a.frankfurt-postgres.render.com/yell_db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
