# Installation Guide

This guide will help you set up the CreateveAI Apache Spark nodes for ComfyUI. We provide two installation methods: Docker (recommended) and manual installation.

## Docker Installation (Recommended)

The Docker installation provides a complete environment with all dependencies pre-configured.

### Prerequisites
- Docker
- Docker Compose
- Git

### Steps

1. Clone the repository:
```bash
git clone https://github.com/createveai/createveai-apachespark.git
cd createveai-apachespark
```

2. Start the environment:
```bash
docker-compose up -d
```

3. Access the services:
- ComfyUI: http://localhost:8181
- Jupyter Lab: http://localhost:8888
- Spark UI: http://localhost:8080

### Container Services

The Docker environment includes:
- **Apache Spark**: Distributed computing engine
- **Jupyter Lab**: Interactive development environment
- **ComfyUI**: Main application with our custom nodes

## Manual Installation

### Prerequisites
- Python 3.10+
- Java 11+
- ComfyUI

### Steps

1. Install ComfyUI if you haven't already:
```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
```

2. Clone our repository into the custom_nodes directory:
```bash
cd custom_nodes
git clone https://github.com/createveai/createveai-apachespark.git
cd createveai-apachespark
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install optional model files:
```bash
python -m spacy download en_core_web_sm
```

## Verifying Installation

1. Start ComfyUI:
```bash
python main.py
```

2. Open your browser and navigate to http://localhost:8188

3. You should see our nodes in the node menu under "CreateveAI/Apache Spark"

## Troubleshooting

### Common Issues

1. **Java Not Found**
   ```
   Error: Java installation not found
   ```
   Solution: Install Java 11 or later:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install openjdk-11-jdk
   
   # macOS
   brew install openjdk@11
   ```

2. **PySpark Installation Failed**
   ```
   Error: Failed building wheel for pyspark
   ```
   Solution: Install build tools:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install build-essential python3-dev
   
   # macOS
   xcode-select --install
   ```

3. **Port Conflicts**
   ```
   Error: Address already in use
   ```
   Solution: Change the ports in docker-compose.yml or stop conflicting services

### Getting Help

If you encounter issues:
1. Check our [FAQ](../faq.md)
2. Search [existing issues](https://github.com/createveai/createveai-apachespark/issues)
3. Create a new issue with:
   - Detailed error message
   - Installation method used
   - System information
   - Steps to reproduce

## Next Steps

- Read the [Configuration Guide](configuration.md)
- Try the [Quick Start Tutorial](quick-start.md)
- Explore [Example Workflows](../examples/)
