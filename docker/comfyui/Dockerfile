FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    python3-dev \
    openjdk-11-jdk \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    COMFYUI_DIR=/comfyui

# Create ComfyUI directory
WORKDIR ${COMFYUI_DIR}

# Clone ComfyUI repository
RUN git clone https://github.com/comfyanonymous/ComfyUI.git .

# Install ComfyUI dependencies
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for our custom nodes
COPY requirements.txt /tmp/createveai_requirements.txt
RUN pip install --no-cache-dir -r /tmp/createveai_requirements.txt

# Create directories for mounting
RUN mkdir -p \
    ${COMFYUI_DIR}/models \
    ${COMFYUI_DIR}/output \
    ${COMFYUI_DIR}/workflows \
    ${COMFYUI_DIR}/custom_nodes

# Copy entrypoint script
COPY docker/comfyui/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8181

ENTRYPOINT ["/entrypoint.sh"]
