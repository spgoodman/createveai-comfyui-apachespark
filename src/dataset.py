from typing import Optional, Dict, List, Union, Any
from pathlib import Path
import json
import numpy as np
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, BinaryType

from .base import Node, SparkConfig, NodeOutput, ValidationError, DataType
from .connection import SessionContext

class Dataset:
    """Wrapper class for Spark DataFrame with metadata"""
    
    def __init__(self, 
                 data: DataFrame, 
                 name: str,
                 metadata: Optional[Dict] = None):
        self.data = data
        self.name = name
        self.metadata = metadata or {}
        
    def persist(self):
        """Persist DataFrame in memory"""
        self.data = self.data.persist()
        return self
    
    def unpersist(self):
        """Unpersist DataFrame from memory"""
        self.data.unpersist()
        return self
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the dataset"""
        self.metadata[key] = value
        return self

class DatasetManager:
    """Manages dataset operations"""
    
    def __init__(self, spark_config: SparkConfig):
        self.spark_config = spark_config
        
    def create_dataset(self, 
                      name: str,
                      schema: Optional[StructType] = None) -> Dataset:
        """Create a new empty dataset"""
        with SessionContext(self.spark_config) as spark:
            if schema is None:
                # Default schema for image datasets
                schema = StructType([
                    StructField("id", StringType(), False),
                    StructField("image_data", BinaryType(), True),
                    StructField("metadata", StringType(), True),
                    StructField("timestamp", StringType(), True)
                ])
            
            empty_df = spark.createDataFrame([], schema)
            return Dataset(empty_df, name)
    
    def load_dataset(self,
                    path: str,
                    format: str = "parquet",
                    options: Optional[Dict[str, str]] = None) -> Dataset:
        """Load dataset from storage"""
        with SessionContext(self.spark_config) as spark:
            reader = spark.read.format(format)
            if options:
                for key, value in options.items():
                    reader = reader.option(key, value)
            
            df = reader.load(path)
            name = Path(path).stem
            
            # Load metadata if exists
            metadata_path = Path(path).parent / f"{name}_metadata.json"
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
            
            return Dataset(df, name, metadata)
    
    def save_dataset(self,
                    dataset: Dataset,
                    path: str,
                    format: str = "parquet",
                    mode: str = "overwrite",
                    options: Optional[Dict[str, str]] = None):
        """Save dataset to storage"""
        writer = dataset.data.write.format(format).mode(mode)
        if options:
            for key, value in options.items():
                writer = writer.option(key, value)
        
        writer.save(path)
        
        # Save metadata
        if dataset.metadata:
            metadata_path = Path(path).parent / f"{dataset.name}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(dataset.metadata, f, indent=2)

class CreateDatasetNode(Node):
    """Node for creating new datasets"""
    
    RETURN_TYPES = (DataType.DATASET,)
    RETURN_NAMES = ("dataset",)
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": "new_dataset"}),
                "connection_type": (["LOCAL", "DATABRICKS"], {"default": "LOCAL"}),
                "master": ("STRING", {"default": "local[*]"}),
                "app_name": ("STRING", {"default": "CreateveAI"})
            },
            "optional": {
                "config_params": ("DICT", {"default": {}})
            }
        }
    
    def execute(self, 
                name: str,
                connection_type: str,
                master: str,
                app_name: str,
                config_params: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        config = SparkConfig(
            connection_type=connection_type,
            master=master,
            app_name=app_name,
            config_params=config_params or {}
        )
        
        manager = DatasetManager(config)
        dataset = manager.create_dataset(name)
        
        return (dataset,)

class LoadDatasetNode(Node):
    """Node for loading datasets"""
    
    RETURN_TYPES = (DataType.DATASET,)
    RETURN_NAMES = ("dataset",)
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {}),
                "format": (["parquet", "delta", "csv"], {"default": "parquet"}),
                "connection_type": (["LOCAL", "DATABRICKS"], {"default": "LOCAL"}),
                "master": ("STRING", {"default": "local[*]"}),
                "app_name": ("STRING", {"default": "CreateveAI"})
            },
            "optional": {
                "config_params": ("DICT", {"default": {}}),
                "options": ("DICT", {"default": {}})
            }
        }
    
    def execute(self,
                path: str,
                format: str,
                connection_type: str,
                master: str,
                app_name: str,
                config_params: Optional[Dict] = None,
                options: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        config = SparkConfig(
            connection_type=connection_type,
            master=master,
            app_name=app_name,
            config_params=config_params or {}
        )
        
        manager = DatasetManager(config)
        dataset = manager.load_dataset(path, format, options)
        
        return (dataset,)

class SaveDatasetNode(Node):
    """Node for saving datasets"""
    
    RETURN_TYPES = (DataType.DATASET,)
    RETURN_NAMES = ("dataset",)
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "dataset": (DataType.DATASET, {}),
                "path": ("STRING", {}),
                "format": (["parquet", "delta", "csv"], {"default": "parquet"}),
                "mode": (["overwrite", "append", "ignore", "error"], {"default": "overwrite"})
            },
            "optional": {
                "options": ("DICT", {"default": {}})
            }
        }
    
    def execute(self,
                dataset: Dataset,
                path: str,
                format: str,
                mode: str,
                options: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        manager = DatasetManager(dataset.data.sparkSession)
        manager.save_dataset(dataset, path, format, mode, options)
        
        return (dataset,)

class FilterDatasetNode(Node):
    """Node for filtering datasets"""
    
    RETURN_TYPES = (DataType.DATASET,)
    RETURN_NAMES = ("filtered_dataset",)
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "dataset": (DataType.DATASET, {}),
                "condition": ("STRING", {})
            }
        }
    
    def execute(self, dataset: Dataset, condition: str) -> tuple:
        """Execute node functionality"""
        filtered_df = dataset.data.filter(condition)
        filtered_dataset = Dataset(
            filtered_df,
            f"{dataset.name}_filtered",
            dataset.metadata
        )
        
        return (filtered_dataset,)
