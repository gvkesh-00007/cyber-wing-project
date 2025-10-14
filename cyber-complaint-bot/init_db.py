# init_db.py
from database import engine, Base
import models  # Ensure models are imported so Base.metadata knows about them

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

if __name__ == "__main__":
    init_db()
