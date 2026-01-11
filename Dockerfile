# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: Sync with exact versions from uv.lock
# --no-dev: Do not install dev dependencies
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY src ./src

# Add the virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Environment variables for Python
ENV PYTHONUNBUFFERED=1

# Expose the MCP server port
EXPOSE 8000

# Run the server
CMD ["python", "-m", "src.server"]
