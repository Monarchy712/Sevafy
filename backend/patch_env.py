import os

files = [
    "c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend/app/main.py", 
    "c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend/app/database.py",
    "c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend/app/auth.py"
]

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Mutate to override=True globally
    content = content.replace(
        "load_dotenv(dotenv_path)", 
        "load_dotenv(dotenv_path, override=True)"
    )
    content = content.replace(
        "load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))", 
        "load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)"
    )
    
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)

print("Environment variable reloading strictly overridden!")
