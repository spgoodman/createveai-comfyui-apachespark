import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import numpy as np

class Node(ABC):
    """Base class for all nodes"""
    
    CATEGORY = "CreateveAI/Apache Spark"
    CATEGORY_ICON = "🔥"  # Spark icon
    VERSION = "1.0.0"
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "execute"
    OUTPUT_NODE = False
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Check if node needs to be re-executed"""
        return float("nan")  # Always update by default
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        """Validate input values before execution"""
        return True
    
    def on_cleanup(self):
        """Cleanup resources when node is deleted"""
        pass

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute node functionality"""
        pass

@dataclass
class SparkConfig:
    """Configuration for Spark connection"""
    connection_type: str  # LOCAL or DATABRICKS
    master: str
    app_name: str
    config_params: Dict[str, Any]

@dataclass
class DatabricksConfig:
    """Configuration for Databricks connection"""
    workspace_url: str
    token: str
    cluster_id: str
    org_id: Optional[str] = None
    
class DataType:
    """Data type definitions for node inputs/outputs"""
    TENSOR = "TENSOR"
    DATASET = "DATASET"
    IMAGE = "IMAGE"
    STRING = "STRING"
    INT = "INT"
    FLOAT = "FLOAT"
    BOOL = "BOOL"
    DICT = "DICT"
    LIST = "LIST"
    ANY = "ANY"

class NodeOutput:
    """Wrapper for node outputs with metadata"""
    def __init__(self, data: Any, metadata: Optional[Dict] = None):
        self.data = data
        self.metadata = metadata or {}

class ValidationError(Exception):
    """Error for input validation failures"""
    pass

def validate_input(value: Any, expected_type: str) -> bool:
    """Validate input value against expected type"""
    if expected_type == DataType.TENSOR:
        return isinstance(value, (np.ndarray, List))
    elif expected_type == DataType.DATASET:
        # Will be implemented with Spark DataFrame validation
        return True
    elif expected_type == DataType.IMAGE:
        # ComfyUI image format validation
        return True
    elif expected_type == DataType.STRING:
        return isinstance(value, str)
    elif expected_type == DataType.INT:
        return isinstance(value, int)
    elif expected_type == DataType.FLOAT:
        return isinstance(value, (int, float))
    elif expected_type == DataType.BOOL:
        return isinstance(value, bool)
    elif expected_type == DataType.DICT:
        return isinstance(value, dict)
    elif expected_type == DataType.LIST:
        return isinstance(value, list)
    elif expected_type == DataType.ANY:
        return True
    return False
