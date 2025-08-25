# Maven Decoder MCP Server Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-jdk \
    wget \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Java will be available on PATH via default-jdk

# Create app directory
WORKDIR /app

# Copy project files
COPY requirements.txt ./
COPY pyproject.toml README.md ./
COPY maven_decoder_mcp ./maven_decoder_mcp
COPY decompilers ./decompilers
COPY setup_decompilers.sh ./

# Install Python dependencies and package
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Create .m2 directory for Maven repository
RUN mkdir -p /home/mcpuser/.m2/repository

# Setup decompilers
RUN chmod +x ./setup_decompilers.sh && \
    ./setup_decompilers.sh

# Expose port (if needed for future web interface)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from maven_decoder_mcp import MavenDecoderServer; print('OK')" || exit 1

# Set default command
CMD ["maven-decoder-mcp"]

# Labels
LABEL maintainer="Ali Tabatabaei <ali79taba@gmail.com>"
LABEL description="MCP server for reading and decompiling Maven .m2 jar files"
LABEL version="1.0.0"
