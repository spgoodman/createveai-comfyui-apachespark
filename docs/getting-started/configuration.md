# Configuration Guide

This guide covers the configuration options for the CreateveAI Apache Spark nodes for ComfyUI.

## Spark Configuration

### Local Mode

By default, the nodes use Spark in local mode. Configuration is stored in `~/.createveai/spark_config.json`:

```json
{
  "local": {
    "master": "local[*]",
    "app_name": "CreateveAI",
    "config_params": {
      "spark.driver.memory": "4g",
      "spark.sql.execution.arrow.enabled": "true"
    }
  }
}
```

#### Configuration Options

- `master`: Spark master URL
  - `local[*]`: Use all available cores
  - `local[n]`: Use n cores
- `app_name`: Application name in Spark UI
- `config_params`: Spark configuration parameters
  - `spark.driver.memory`: Driver process memory
  - `spark.executor.memory`: Executor process memory
  - `spark.sql.execution.arrow.enabled`: Enable Arrow optimization

### Databricks Mode

To use Databricks, configure your credentials in the same config file:

```json
{
  "databricks": {
    "workspace_url": "https://your-workspace.cloud.databricks.com",
    "token": "your-access-token",
    "cluster_id": "your-cluster-id",
    "org_id": "your-org-id"  // Optional
  }
}
```

#### Getting Databricks Credentials

1. Generate an access token:
   - Go to User Settings in Databricks
   - Click "Generate New Token"
   - Copy the token value

2. Get cluster information:
   - Go to Compute in Databricks
   - Select your cluster
   - Copy the cluster ID from the URL

## Node Configuration

### Dataset Nodes

#### CreateDatasetNode
```python
{
    "name": "new_dataset",
    "connection_type": "LOCAL",  # or "DATABRICKS"
    "master": "local[*]",
    "app_name": "CreateveAI",
    "config_params": {
        "spark.driver.memory": "4g"
    }
}
```

#### LoadDatasetNode
```python
{
    "path": "/path/to/data",
    "format": "parquet",  # or "delta", "csv"
    "options": {
        "header": "true",  # for CSV
        "inferSchema": "true"
    }
}
```

### Feature Extraction Nodes

#### TextFeatureExtractorNode
```python
{
    "model_config": {
        "model_name": "all-MiniLM-L6-v2",
        "max_length": 512
    },
    "feature_config": {
        "batch_size": 32,
        "cache_results": true
    }
}
```

#### ImageFeatureAnalyzerNode
```python
{
    "model_config": {},
    "feature_config": {
        "batch_size": 16,
        "cache_results": true,
        "use_gpu": true
    }
}
```

## Environment Variables

The following environment variables can be used to override configuration:

```bash
# Spark Configuration
SPARK_MASTER_URL=spark://localhost:7077
SPARK_DRIVER_MEMORY=4g
SPARK_EXECUTOR_MEMORY=4g

# Databricks Configuration
DATABRICKS_HOST=your-workspace-url
DATABRICKS_TOKEN=your-access-token
DATABRICKS_CLUSTER_ID=your-cluster-id
DATABRICKS_ORG_ID=your-org-id

# Feature Extraction
FEATURE_EXTRACTION_BATCH_SIZE=32
FEATURE_EXTRACTION_USE_GPU=true
```

## Docker Environment

When using Docker, configure the environment in `docker-compose.yml`:

```yaml
services:
  spark:
    environment:
      - SPARK_MODE=master
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no

  comfyui:
    environment:
      - SPARK_MASTER=spark://spark:7077
```

## Performance Tuning

### Memory Configuration

1. Driver Memory:
```python
config_params = {
    "spark.driver.memory": "4g",
    "spark.driver.maxResultSize": "2g"
}
```

2. Executor Memory:
```python
config_params = {
    "spark.executor.memory": "4g",
    "spark.executor.memoryOverhead": "1g"
}
```

### Caching Strategy

1. Memory Only:
```python
cache_strategy = "MEMORY"
```

2. Memory and Disk:
```python
cache_strategy = "MEMORY_AND_DISK"
```

### Batch Processing

1. Text Feature Extraction:
```python
feature_config = {
    "batch_size": 32,
    "cache_results": true
}
```

2. Image Feature Analysis:
```python
feature_config = {
    "batch_size": 16,
    "use_gpu": true
}
```

## Security Configuration

### Local Mode Security
```python
config_params = {
    "spark.authenticate": "true",
    "spark.authenticate.secret": "your-secret"
}
```

### Databricks Security
```python
config_params = {
    "spark.databricks.token": "your-token",
    "spark.databricks.workspace.token.enabled": "true"
}
```

## Next Steps

- Try the [Quick Start Tutorial](quick-start.md)
- Learn about [Node Types](../nodes/README.md)
- See [Example Workflows](../examples/README.md)
