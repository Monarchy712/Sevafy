# Stage 1: Build the React Frontend
FROM node:18-alpine AS build-stage
WORKDIR /app
# Copy package files and install dependencies
COPY package*.json ./
RUN npm install
# Copy the rest of the frontend source and build
COPY . .
RUN npm run build

# Stage 2: Run the FastAPI Backend
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

# Copy the compiled frontend files from the build-stage
# In main.py, we set dist_path = os.path.join(os.path.dirname(__file__), "..", "dist")
# Since main.py is in /app/backend/app/main.py, ".." is /app/backend/dist
COPY --from=build-stage /app/dist ./dist

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
