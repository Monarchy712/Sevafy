import sys
import os
sys.path.append(os.path.abspath('c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend'))

from app.database import Base, engine
# IMPORT ALL MODELS to populate Base.metadata!
from app import models 

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
