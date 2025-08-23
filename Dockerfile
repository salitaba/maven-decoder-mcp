# Maven Decoder MCP Server Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Create app directory
WORKDIR /app

# Copy package files
COPY dist/maven_decoder_mcp-1.0.0-py3-none-any.whl .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir maven_decoder_mcp-1.0.0-py3-none-any.whl

# Install MCP SDK directly from GitHub
RUN pip install --no-cache-dir git+https://github.com/modelcontextprotocol/python-sdk.git

# Create non-root user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Create .m2 directory for Maven repository
RUN mkdir -p /home/mcpuser/.m2/repository

# Setup decompilers
RUN maven-decoder-setup

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
