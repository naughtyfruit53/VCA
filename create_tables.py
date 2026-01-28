"""Create database tables."""
from app.config.database import engine, Base
from app.models import Tenant, PhoneNumber, Call, AIProfile

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✓ Tables created successfully")
