# Node Reference

This document provides detailed information about all available nodes in the CreateveAI Apache Spark integration for ComfyUI.

## Dataset Nodes

### CreateDatasetNode

Creates a new empty dataset with a specified schema.

**Inputs:**
- `name` (STRING): Name of the dataset
- `connection_type` (["LOCAL", "DATABRICKS"]): Type of Spark connection
- `master` (STRING): Spark master URL
- `app_name` (STRING): Application name
- `config_params` (DICT, optional): Additional Spark configuration

**Outputs:**
- `dataset`: Created dataset object

**Example:**
```python
{
    "name": "my_dataset",
    "connection_type": "LOCAL",
    "master": "local[*]",
    "app_name": "CreateveAI",
    "config_params": {
        "spark.driver.memory": "4g"
    }
}
```

### LoadDatasetNode

Loads a dataset from storage.

**Inputs:**
- `path` (STRING): Path to dataset
- `format` (["parquet", "delta", "csv"]): File format
- `connection_type` (["LOCAL", "DATABRICKS"]): Type of Spark connection
- `master` (STRING): Spark master URL
- `app_name` (STRING): Application name
- `config_params` (DICT, optional): Additional configuration
- `options` (DICT, optional): Format-specific options

**Outputs:**
- `dataset`: Loaded dataset object

**Example:**
```python
{
    "path": "/data/my_dataset.parquet",
    "format": "parquet",
    "connection_type": "LOCAL",
    "options": {
        "mergeSchema": "true"
    }
}
```

### SaveDatasetNode

Saves a dataset to storage.

**Inputs:**
- `dataset` (DATASET): Dataset to save
- `path` (STRING): Save location
- `format` (["parquet", "delta", "csv"]): Output format
- `mode` (["overwrite", "append", "ignore", "error"]): Save mode
- `options` (DICT, optional): Format-specific options

**Outputs:**
- `dataset`: Input dataset (for chaining)

**Example:**
```python
{
    "path": "/output/dataset",
    "format": "delta",
    "mode": "overwrite",
    "options": {
        "compression": "snappy"
    }
}
```

### FilterDatasetNode

Filters a dataset using SQL conditions.

**Inputs:**
- `dataset` (DATASET): Input dataset
- `condition` (STRING): SQL filter condition

**Outputs:**
- `filtered_dataset`: Filtered dataset

**Example:**
```python
{
    "condition": "age > 25 AND city = 'New York'"
}
```

## Query Nodes

### TableInspectorNode

Inspects table schema and provides sample data.

**Inputs:**
- `connection_type` (["LOCAL", "DATABRICKS"]): Connection type
- `database_name` (STRING): Database name
- `table_name` (STRING): Table name
- `update_trigger` (BOOLEAN): Force update
- `config_params` (DICT, optional): Additional configuration

**Outputs:**
- `table_schema`: Table schema information
- `column_types`: Column data types
- `sample_data`: Sample records
- `schema_hash`: Schema version hash

### DynamicQueryBuilderNode

Builds SQL queries dynamically.

**Inputs:**
- `table_schema` (DICT): Table schema
- `schema_hash` (STRING): Schema version
- `selected_columns` (LIST): Columns to select
- `conditions` (LIST): Filter conditions
- `update_trigger` (BOOLEAN): Force update
- `aggregations` (LIST, optional): Aggregation operations
- `group_by` (LIST, optional): Grouping columns
- `order_by` (LIST, optional): Sorting specification

**Outputs:**
- `query_spec`: Query specification
- `preview_sql`: SQL preview

### UniversalQueryExecutorNode

Executes queries with caching support.

**Inputs:**
- `connection_type` (["LOCAL", "DATABRICKS"]): Connection type
- `database_name` (STRING): Database name
- `table_name` (STRING): Table name
- `query_spec` (DICT): Query specification
- `update_trigger` (BOOLEAN): Force update
- `cache_strategy` (["NONE", "MEMORY", "DISK"]): Caching strategy
- `config_params` (DICT, optional): Additional configuration

**Outputs:**
- `result_dataset`: Query results
- `affected_rows`: Number of rows
- `execution_stats`: Execution statistics

## Feature Extraction Nodes

### TextFeatureExtractorNode

Extracts features from text data.

**Inputs:**
- `dataset` (DATASET): Input dataset
- `text_column` (STRING): Column containing text
- `extraction_type` (["SEMANTIC_VECTORS", "KEYWORDS", "ENTITIES", "SENTIMENT", "TOPICS"]): Type of extraction
- `model_config` (DICT, optional): Model configuration
- `feature_config` (DICT, optional): Feature extraction configuration

**Outputs:**
- `features`: Extracted features
- `metadata`: Processing metadata
- `prompt_suggestions`: Generated prompt suggestions

**Example:**
```python
{
    "text_column": "description",
    "extraction_type": "SEMANTIC_VECTORS",
    "model_config": {
        "model_name": "all-MiniLM-L6-v2",
        "max_length": 512
    }
}
```

### ImageFeatureAnalyzerNode

Analyzes image features.

**Inputs:**
- `dataset` (DATASET): Input dataset
- `image_column` (STRING): Column containing images
- `analysis_types` (["COMPOSITION", "COLOR_PALETTE", "OBJECTS", "STYLE", "AESTHETICS"]): Types of analysis
- `model_config` (DICT, optional): Model configuration
- `feature_config` (DICT, optional): Analysis configuration

**Outputs:**
- `visual_features`: Extracted visual features
- `style_vectors`: Style analysis vectors
- `suggested_params`: Suggested parameters

**Example:**
```python
{
    "image_column": "image_data",
    "analysis_types": ["COMPOSITION", "STYLE"],
    "feature_config": {
        "batch_size": 16,
        "use_gpu": true
    }
}
```

### FeatureCombinerNode

Combines text and image features.

**Inputs:**
- `text_features` (TENSOR): Text features
- `image_features` (TENSOR): Image features
- `combination_method` (["CONCAT", "WEIGHTED", "CROSS_ATTENTION"]): Combination method
- `weights` (DICT, optional): Feature weights

**Outputs:**
- `combined_features`: Combined feature tensor
- `metadata`: Combination metadata

**Example:**
```python
{
    "combination_method": "CROSS_ATTENTION",
    "weights": {
        "text": 0.6,
        "image": 0.4
    }
}
```

## Best Practices

1. **Memory Management**
   - Use appropriate batch sizes
   - Enable caching strategically
   - Monitor memory usage in Spark UI

2. **Performance Optimization**
   - Choose efficient file formats (Parquet/Delta)
   - Use column pruning and filtering
   - Leverage Spark's optimization capabilities

3. **Error Handling**
   - Check input data quality
   - Handle null values appropriately
   - Monitor execution statistics

4. **Feature Extraction**
   - Balance batch size and memory
   - Use GPU when available
   - Cache frequently used features

## See Also

- [Configuration Guide](../getting-started/configuration.md)
- [Example Workflows](../examples/README.md)
- [API Reference](../api/README.md)
