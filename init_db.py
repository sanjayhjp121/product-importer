"""Initialize database tables."""
from app.database import engine, Base
from app.models import Product, Webhook

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

