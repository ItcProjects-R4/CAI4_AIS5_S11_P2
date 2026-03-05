FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Create a non-root user for security
RUN groupadd -r etl && useradd -r -g etl etl

# Install system packages needed for pyodbc (ODBC drivers)
# Note: Full ODBC driver installation may require msodbcsql package
# For development, dependencies may not be available, and that's okay.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY --chown=etl:etl . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .[dev]

# Switch to non-root user
USER etl

# Default entrypoint - can be overridden
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["--help"]
