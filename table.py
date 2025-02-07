"""
Dynamic table inspection and query nodes for ComfyUI
"""

from typing import Optional, Dict, List, Any, Tuple
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType

from .base import Node, SparkConfig, NodeOutput, ValidationError, DataType
from .connection import SessionContext
from .dataset import Dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamicTableInspectorNode(Node):
    """Node for inspecting table schema with auto-update capability"""
    
    RETURN_TYPES = (DataType.DICT, DataType.DICT, DataType.DICT)
    RETURN_NAMES = ("table_schema", "column_info", "sample_data")
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "connection_type": (["LOCAL", "DATABRICKS"], {"default": "LOCAL"}),
                "database_name": ("STRING", {}),
                "table_name": ("STRING", {}),
                "update_trigger": ("BOOLEAN", {"default": False})
            },
            "optional": {
                "config_params": ("DICT", {"default": {}})
            }
        }
    
    def _get_schema_info(self, df: DataFrame) -> Tuple[Dict, Dict]:
        """Extract schema information from DataFrame"""
        schema_dict = {}
        column_info = {}
        
        for field in df.schema.fields:
            schema_dict[field.name] = {
                "type": str(field.dataType),
                "nullable": field.nullable,
                "metadata": field.metadata
            }
            
            # Get column statistics
            stats = df.select([
                F.count(field.name).alias("count"),
                F.countDistinct(field.name).alias("distinct"),
                F.min(field.name).alias("min"),
                F.max(field.name).alias("max")
            ]).collect()[0]
            
            column_info[field.name] = {
                "total_count": stats["count"],
                "distinct_count": stats["distinct"],
                "min_value": stats["min"],
                "max_value": stats["max"],
                "sample_values": [row[field.name] for row in df.select(field.name).limit(5).collect()]
            }
        
        return schema_dict, column_info
    
    def execute(self,
                connection_type: str,
                database_name: str,
                table_name: str,
                update_trigger: bool,
                config_params: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        config = SparkConfig(
            connection_type=connection_type,
            master="local[*]",
            app_name="TableInspector",
            config_params=config_params or {}
        )
        
        try:
            with SessionContext(config) as spark:
                # Get table
                df = spark.table(f"{database_name}.{table_name}")
                
                # Get schema information
                schema_dict, column_info = self._get_schema_info(df)
                
                # Get sample data
                sample_data = df.limit(5).toPandas().to_dict('records')
                
                return (schema_dict, column_info, sample_data)
                
        except Exception as e:
            logger.error(f"Error inspecting table: {str(e)}")
            raise ValidationError(f"Failed to inspect table: {str(e)}")

class DynamicQueryNode(Node):
    """Node for building and executing dynamic queries"""
    
    RETURN_TYPES = (DataType.DATASET, DataType.DICT)
    RETURN_NAMES = ("result_dataset", "query_info")
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "connection_type": (["LOCAL", "DATABRICKS"], {"default": "LOCAL"}),
                "database_name": ("STRING", {}),
                "table_name": ("STRING", {}),
                "selected_columns": (DataType.LIST, {}),
                "conditions": (DataType.LIST, {"default": []}),
                "update_trigger": ("BOOLEAN", {"default": False})
            },
            "optional": {
                "group_by": (DataType.LIST, {"default": []}),
                "order_by": (DataType.LIST, {"default": []}),
                "limit": ("INT", {"default": 1000}),
                "config_params": ("DICT", {"default": {}})
            }
        }
    
    def _build_query(self,
                     df: DataFrame,
                     selected_columns: List[str],
                     conditions: List[str],
                     group_by: List[str],
                     order_by: List[str],
                     limit: int) -> DataFrame:
        """Build and execute query"""
        # Select columns
        if selected_columns:
            df = df.select(*selected_columns)
        
        # Apply filters
        for condition in conditions:
            df = df.filter(condition)
        
        # Apply grouping
        if group_by:
            df = df.groupBy(*group_by)
        
        # Apply ordering
        if order_by:
            order_exprs = []
            for order in order_by:
                col = order["column"]
                if order.get("direction", "ASC").upper() == "DESC":
                    col = F.desc(col)
                order_exprs.append(col)
            df = df.orderBy(*order_exprs)
        
        # Apply limit
        if limit > 0:
            df = df.limit(limit)
        
        return df
    
    def execute(self,
                connection_type: str,
                database_name: str,
                table_name: str,
                selected_columns: List[str],
                conditions: List[str],
                update_trigger: bool,
                group_by: Optional[List[str]] = None,
                order_by: Optional[List[Dict]] = None,
                limit: int = 1000,
                config_params: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        config = SparkConfig(
            connection_type=connection_type,
            master="local[*]",
            app_name="DynamicQuery",
            config_params=config_params or {}
        )
        
        try:
            with SessionContext(config) as spark:
                # Get base table
                df = spark.table(f"{database_name}.{table_name}")
                
                # Build and execute query
                start_time = time.time()
                result_df = self._build_query(
                    df,
                    selected_columns,
                    conditions,
                    group_by or [],
                    order_by or [],
                    limit
                )
                
                # Create result dataset
                result_dataset = Dataset(
                    result_df,
                    f"query_result_{database_name}_{table_name}",
                    {
                        "source_table": f"{database_name}.{table_name}",
                        "query_params": {
                            "selected_columns": selected_columns,
                            "conditions": conditions,
                            "group_by": group_by,
                            "order_by": order_by,
                            "limit": limit
                        }
                    }
                )
                
                # Get query information
                query_info = {
                    "input_rows": df.count(),
                    "output_rows": result_df.count(),
                    "execution_time": time.time() - start_time,
                    "spark_plan": result_df._jdf.queryExecution().toString()
                }
                
                return (result_dataset, query_info)
                
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise ValidationError(f"Failed to execute query: {str(e)}")

class QueryTemplateNode(Node):
    """Node for managing and executing query templates"""
    
    RETURN_TYPES = (DataType.DICT, DataType.DICT)
    RETURN_NAMES = ("query_spec", "template_info")
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template_name": ("STRING", {}),
                "template_parameters": (DataType.DICT, {}),
                "table_schema": (DataType.DICT, {}),
                "update_trigger": ("BOOLEAN", {"default": False})
            }
        }
    
    def _validate_template(self,
                          template_name: str,
                          parameters: Dict,
                          schema: Dict) -> None:
        """Validate template and parameters"""
        # Template validation would be implemented here
        pass
    
    def _build_query_spec(self,
                         template_name: str,
                         parameters: Dict,
                         schema: Dict) -> Dict:
        """Build query specification from template"""
        # Template processing would be implemented here
        query_spec = {
            "template": template_name,
            "parameters": parameters,
            "generated_sql": "SELECT * FROM table"  # Placeholder
        }
        return query_spec
    
    def execute(self,
                template_name: str,
                template_parameters: Dict,
                table_schema: Dict,
                update_trigger: bool) -> tuple:
        """Execute node functionality"""
        try:
            # Validate template
            self._validate_template(template_name, template_parameters, table_schema)
            
            # Build query specification
            query_spec = self._build_query_spec(
                template_name,
                template_parameters,
                table_schema
            )
            
            # Template information
            template_info = {
                "name": template_name,
                "parameter_count": len(template_parameters),
                "validation_status": "valid"
            }
            
            return (query_spec, template_info)
            
        except Exception as e:
            logger.error(f"Error processing template: {str(e)}")
            raise ValidationError(f"Failed to process template: {str(e)}")
