from backend.db import engine
from backend.models import SQLModel

print("Creating tables...")
SQLModel.metadata.create_all(engine)
print("Table created!")
