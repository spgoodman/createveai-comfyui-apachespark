# API Reference

This document provides detailed information about the internal APIs and architecture of the CreateveAI Apache Spark nodes for ComfyUI.

## Core Components

### Base Classes

#### Node
```python
class Node(ABC):
    """Base class for all nodes"""
    
    CATEGORY: str  # Node category in ComfyUI
    CATEGORY_ICON: str  # Category icon
    VERSION: str  # Node version
    RETURN_TYPES: tuple  # Output types
    RETURN_NAMES: tuple  # Output names
    FUNCTION: str  # Execution function name
    OUTPUT_NODE: bool  # Is output node
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute node functionality"""
        pass
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Check if node needs update"""
        pass
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        """Validate input values"""
        pass
```

#### SparkConfig
```python
@dataclass
class SparkConfig:
    """Configuration for Spark connection"""
    connection_type: str  # LOCAL or DATABRICKS
    master: str  # Spark master URL
    app_name: str  # Application name
    config_params: Dict[str, Any]  # Additional configuration
```

#### Dataset
```python
class Dataset:
    """Wrapper for Spark DataFrame"""
    
    def __init__(self, data: DataFrame, name: str, metadata: Optional[Dict] = None):
        self.data = data  # Spark DataFrame
        self.name = name  # Dataset name
        self.metadata = metadata or {}  # Additional metadata
    
    def persist(self) -> 'Dataset':
        """Persist DataFrame in memory"""
        pass
    
    def unpersist(self) -> 'Dataset':
        """Unpersist DataFrame from memory"""
        pass
```

### Connection Management

#### SparkConnectionManager
```python
class SparkConnectionManager:
    """Manages Spark connections and sessions"""
    
    def get_session(self, config: SparkConfig) -> SparkSession:
        """Get or create a Spark session"""
        pass
    
    def stop_session(self):
        """Stop the current Spark session"""
        pass
    
    def update_databricks_config(self, config: DatabricksConfig):
        """Update Databricks configuration"""
        pass
```

#### SessionContext
```python
class SessionContext:
    """Context manager for Spark sessions"""
    
    def __enter__(self) -> SparkSession:
        """Enter context and get session"""
        pass
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        pass
```

### UI Components

#### ProgressTracker
```python
class ProgressTracker:
    """Track progress of node operations"""
    
    def start_operation(self, operation_id: str, text: str = "Starting..."):
        """Start tracking an operation"""
        pass
    
    def update_progress(self, operation_id: str, value: float, text: Optional[str] = None):
        """Update operation progress"""
        pass
    
    def complete_operation(self, operation_id: str, text: str = "Completed"):
        """Mark operation as completed"""
        pass
```

#### NodeWidgetMixin
```python
class NodeWidgetMixin:
    """Mixin for adding widget support to nodes"""
    
    @classmethod
    def add_widget(cls, name: str, widget_type: str, default: Any = None, 
                  options: Optional[Dict] = None) -> Dict:
        """Add a widget configuration"""
        pass
    
    @classmethod
    def add_combo_widget(cls, name: str, choices: list, default: Any = None,
                        options: Optional[Dict] = None) -> Dict:
        """Add a combo box widget"""
        pass
```

## Feature Extraction

### Text Features

#### TextFeatureExtractor
```python
class TextFeatureExtractor:
    """Extract features from text data"""
    
    def extract_semantic_vectors(self, texts: List[str], model_config: Dict) -> np.ndarray:
        """Extract semantic vectors using transformers"""
        pass
    
    def extract_keywords(self, texts: List[str], model_config: Dict) -> List[Dict]:
        """Extract keywords from texts"""
        pass
    
    def extract_entities(self, texts: List[str], model_config: Dict) -> List[Dict]:
        """Extract named entities from texts"""
        pass
```

### Image Features

#### ImageFeatureAnalyzer
```python
class ImageFeatureAnalyzer:
    """Analyze image features"""
    
    def analyze_composition(self, image: Image.Image) -> Dict:
        """Analyze image composition"""
        pass
    
    def extract_color_palette(self, image: Image.Image, num_colors: int = 5) -> Dict:
        """Extract dominant color palette"""
        pass
    
    def detect_objects(self, image: Image.Image) -> Dict:
        """Detect objects in image"""
        pass
```

## Query Building

### QueryBuilder
```python
class QueryBuilder:
    """Build Spark SQL queries"""
    
    def build_query_spec(self, table_schema: Dict, selected_columns: List[str],
                        conditions: List[str], **kwargs) -> Dict:
        """Build query specification"""
        pass
    
    def generate_preview_sql(self, query_spec: Dict) -> str:
        """Generate SQL preview from query spec"""
        pass
```

## Extension Points

### Creating Custom Nodes

1. Inherit from `Node` base class:
```python
class CustomNode(Node):
    CATEGORY = "CreateveAI/Apache Spark"
    RETURN_TYPES = ("DATASET",)
    RETURN_NAMES = ("output_dataset",)
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "param1": ("STRING", {})
            }
        }
    
    def execute(self, param1: str) -> tuple:
        # Implementation
        pass
```

2. Add progress tracking:
```python
from .ui_utils import with_progress

class CustomNode(Node):
    @with_progress("custom_operation")
    def execute(self, param1: str) -> tuple:
        # Implementation with progress updates
        pass
```

### Custom Feature Extractors

1. Create feature extractor class:
```python
class CustomFeatureExtractor:
    def __init__(self, config: Dict):
        self.config = config
    
    def extract_features(self, data: Any) -> np.ndarray:
        # Implementation
        pass
```

2. Register with feature extraction system:
```python
FEATURE_EXTRACTORS = {
    "CUSTOM": CustomFeatureExtractor
}
```

## Best Practices

### Error Handling
```python
try:
    # Operation
    pass
except ValidationError as e:
    # Handle validation errors
    pass
except SparkException as e:
    # Handle Spark errors
    pass
finally:
    # Cleanup
    pass
```

### Memory Management
```python
with SessionContext(config) as spark:
    df = spark.read.parquet(path)
    df = df.persist()  # Cache if needed
    try:
        # Process data
        pass
    finally:
        df.unpersist()  # Always clean up
```

### Progress Updates
```python
@with_progress("operation_name")
def long_running_operation(self):
    tracker = self._progress_tracker
    for i, item in enumerate(items):
        # Process item
        tracker.update_progress(
            "operation_name",
            value=i/len(items),
            text=f"Processing item {i+1}/{len(items)}"
        )
```

## See Also

- [Node Reference](../nodes/README.md)
- [Configuration Guide](../getting-started/configuration.md)
- [Contributing Guide](../../CONTRIBUTING.md)
