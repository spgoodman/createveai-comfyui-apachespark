"""
CreateveAI Apache Spark nodes for ComfyUI
"""

from .dataset import (
    CreateDatasetNode,
    LoadDatasetNode,
    SaveDatasetNode,
    FilterDatasetNode
)

from .query import (
    TableInspectorNode,
    DynamicQueryBuilderNode,
    UniversalQueryExecutorNode
)

from .features import (
    TextFeatureExtractorNode,
    ImageFeatureAnalyzerNode,
    FeatureCombinerNode
)

from .table import (
    DynamicTableInspectorNode,
    DynamicQueryNode,
    QueryTemplateNode
)

NODE_CLASS_MAPPINGS = {
    # Dataset nodes
    "CreateDataset": CreateDatasetNode,
    "LoadDataset": LoadDatasetNode,
    "SaveDataset": SaveDatasetNode,
    "FilterDataset": FilterDatasetNode,
    
    # Query nodes
    "TableInspector": TableInspectorNode,
    "DynamicQueryBuilder": DynamicQueryBuilderNode,
    "UniversalQueryExecutor": UniversalQueryExecutorNode,
    
    # Feature extraction nodes
    "TextFeatureExtractor": TextFeatureExtractorNode,
    "ImageFeatureAnalyzer": ImageFeatureAnalyzerNode,
    "FeatureCombiner": FeatureCombinerNode,
    
    # Dynamic table nodes
    "DynamicTableInspector": DynamicTableInspectorNode,
    "DynamicQuery": DynamicQueryNode,
    "QueryTemplate": QueryTemplateNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # Dataset nodes
    "CreateDataset": "Create Dataset",
    "LoadDataset": "Load Dataset",
    "SaveDataset": "Save Dataset",
    "FilterDataset": "Filter Dataset",
    
    # Query nodes
    "TableInspector": "Table Inspector",
    "DynamicQueryBuilder": "Dynamic Query Builder",
    "UniversalQueryExecutor": "Universal Query Executor",
    
    # Feature extraction nodes
    "TextFeatureExtractor": "Text Feature Extractor",
    "ImageFeatureAnalyzer": "Image Feature Analyzer",
    "FeatureCombiner": "Feature Combiner",
    
    # Dynamic table nodes
    "DynamicTableInspector": "Dynamic Table Inspector",
    "DynamicQuery": "Dynamic Query",
    "QueryTemplate": "Query Template"
}

# Version information
__version__ = "0.1.0"
