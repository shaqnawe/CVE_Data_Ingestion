# create_tables.py
from db import engine
from models import SQLModel

print("Creating tables...")
SQLModel.metadata.create_all(engine)
print("Table created!")
