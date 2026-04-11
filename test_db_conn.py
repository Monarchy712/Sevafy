import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv('backend/.env')
url = os.environ.get("DATABASE_URL")
print(f"Testing connection to: {url.split('@')[-1]}") # Print only the host part for safety

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        print("Successfully connected to the database!")
except Exception as e:
    print(f"Connection failed: {e}")
