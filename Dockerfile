FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy only the files needed for dependency resolution first
# This maximizes Docker cache usage for dependencies
COPY pyproject.toml uv.lock ./

# Sync dependencies using uv
# This maximizes Docker cache usage for dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Command to run the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
