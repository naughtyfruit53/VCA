"""Create database tables."""
from app.config.database import engine, Base
from app.models import User, Tenant, PhoneNumber, Call, AIProfile, BusinessProfile

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✓ Tables created successfully")
