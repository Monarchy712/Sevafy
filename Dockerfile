# Pehle frontend build karo (Stage 1)
FROM node:22-alpine AS build-stage
WORKDIR /app
# Package files copy karke install phero
COPY package*.json ./
RUN npm install
# Baaki saara saaman copy karo aur build maro
COPY . .
RUN npm run build

# Ab backend ki baari (Stage 2)
FROM python:3.11-slim
WORKDIR /app/backend
# Install system dependencies if any are needed for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source
COPY backend/ .

# Compiled frontend files backend folder ke 'dist' mein daal do
# main.py expects it at /app/backend/dist
COPY --from=build-stage /app/dist ./dist

# Expose the port FastAPI runs on
EXPOSE 8080

# Railway automatically handles PORT, exposing 8080 as default

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
