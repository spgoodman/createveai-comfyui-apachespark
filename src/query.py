from typing import Optional, Dict, List, Any, Tuple
import hashlib
import json
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

from .base import Node, SparkConfig, NodeOutput, ValidationError, DataType
from .connection import SessionContext
from .dataset import Dataset

class TableInspectorNode(Node):
    """Node for inspecting table schema with auto-update capability"""
    
    RETURN_TYPES = (DataType.DICT, DataType.DICT, DataType.DICT, DataType.STRING)
    RETURN_NAMES = ("table_schema", "column_types", "sample_data", "schema_hash")
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
    
    def _compute_schema_hash(self, schema: Dict) -> str:
        """Compute hash of schema for change detection"""
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()
    
    def _get_schema_info(self, df: DataFrame) -> Tuple[Dict, Dict]:
        """Extract schema information from DataFrame"""
        schema_dict = {}
        types_dict = {}
        
        for field in df.schema.fields:
            schema_dict[field.name] = {
                "type": str(field.dataType),
                "nullable": field.nullable,
                "metadata": field.metadata
            }
            types_dict[field.name] = str(field.dataType)
        
        return schema_dict, types_dict
    
    def execute(self,
                connection_type: str,
                database_name: str,
                table_name: str,
                update_trigger: bool,
                config_params: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        config = SparkConfig(
            connection_type=connection_type,
            master="local[*]",  # Default for inspection
            app_name="TableInspector",
            config_params=config_params or {}
        )
        
        with SessionContext(config) as spark:
            # Get table
            df = spark.table(f"{database_name}.{table_name}")
            
            # Get schema information
            schema_dict, types_dict = self._get_schema_info(df)
            
            # Get sample data
            sample_data = df.limit(5).toPandas().to_dict('records')
            
            # Compute schema hash
            schema_hash = self._compute_schema_hash(schema_dict)
            
            return (schema_dict, types_dict, sample_data, schema_hash)

class DynamicQueryBuilderNode(Node):
    """Node for building queries dynamically"""
    
    RETURN_TYPES = (DataType.DICT, DataType.STRING)
    RETURN_NAMES = ("query_spec", "preview_sql")
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "table_schema": (DataType.DICT, {}),
                "schema_hash": (DataType.STRING, {}),
                "selected_columns": (DataType.LIST, {}),
                "conditions": (DataType.LIST, {"default": []}),
                "update_trigger": ("BOOLEAN", {"default": False})
            },
            "optional": {
                "aggregations": (DataType.LIST, {"default": []}),
                "group_by": (DataType.LIST, {"default": []}),
                "order_by": (DataType.LIST, {"default": []})
            }
        }
    
    def _validate_columns(self, columns: List[str], schema: Dict) -> None:
        """Validate column names against schema"""
        schema_columns = set(schema.keys())
        invalid_columns = set(columns) - schema_columns
        if invalid_columns:
            raise ValidationError(f"Invalid columns: {invalid_columns}")
    
    def _build_query_spec(self,
                         table_schema: Dict,
                         selected_columns: List[str],
                         conditions: List[str],
                         aggregations: Optional[List[Dict]] = None,
                         group_by: Optional[List[str]] = None,
                         order_by: Optional[List[Dict]] = None) -> Dict:
        """Build query specification"""
        self._validate_columns(selected_columns, table_schema)
        
        query_spec = {
            "select": selected_columns,
            "where": conditions,
            "aggregations": aggregations or [],
            "group_by": group_by or [],
            "order_by": order_by or []
        }
        
        return query_spec
    
    def _generate_preview_sql(self, query_spec: Dict) -> str:
        """Generate SQL preview from query spec"""
        sql_parts = ["SELECT"]
        
        # SELECT clause
        if query_spec["aggregations"]:
            select_items = []
            for agg in query_spec["aggregations"]:
                select_items.append(
                    f"{agg['function']}({agg['column']}) AS {agg['alias']}"
                )
            sql_parts.append(", ".join(select_items))
        else:
            sql_parts.append(", ".join(query_spec["select"]))
        
        # FROM clause will be added by executor
        sql_parts.append("FROM ${table}")
        
        # WHERE clause
        if query_spec["where"]:
            sql_parts.append("WHERE " + " AND ".join(query_spec["where"]))
        
        # GROUP BY clause
        if query_spec["group_by"]:
            sql_parts.append("GROUP BY " + ", ".join(query_spec["group_by"]))
        
        # ORDER BY clause
        if query_spec["order_by"]:
            order_items = []
            for order in query_spec["order_by"]:
                direction = order.get("direction", "ASC")
                order_items.append(f"{order['column']} {direction}")
            sql_parts.append("ORDER BY " + ", ".join(order_items))
        
        return "\n".join(sql_parts)
    
    def execute(self,
                table_schema: Dict,
                schema_hash: str,
                selected_columns: List[str],
                conditions: List[str],
                update_trigger: bool,
                aggregations: Optional[List[Dict]] = None,
                group_by: Optional[List[str]] = None,
                order_by: Optional[List[Dict]] = None) -> tuple:
        """Execute node functionality"""
        query_spec = self._build_query_spec(
            table_schema,
            selected_columns,
            conditions,
            aggregations,
            group_by,
            order_by
        )
        
        preview_sql = self._generate_preview_sql(query_spec)
        
        return (query_spec, preview_sql)

class UniversalQueryExecutorNode(Node):
    """Node for executing dynamic queries"""
    
    RETURN_TYPES = (DataType.DATASET, DataType.INT, DataType.DICT)
    RETURN_NAMES = ("result_dataset", "affected_rows", "execution_stats")
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "connection_type": (["LOCAL", "DATABRICKS"], {"default": "LOCAL"}),
                "database_name": ("STRING", {}),
                "table_name": ("STRING", {}),
                "query_spec": (DataType.DICT, {}),
                "update_trigger": ("BOOLEAN", {"default": False})
            },
            "optional": {
                "cache_strategy": (["NONE", "MEMORY", "DISK"], {"default": "NONE"}),
                "config_params": ("DICT", {"default": {}})
            }
        }
    
    def _apply_query_spec(self, df: DataFrame, query_spec: Dict) -> DataFrame:
        """Apply query specification to DataFrame"""
        # Select columns
        if query_spec["select"]:
            df = df.select(*query_spec["select"])
        
        # Apply filters
        for condition in query_spec["where"]:
            df = df.filter(condition)
        
        # Apply aggregations
        if query_spec["aggregations"]:
            agg_exprs = []
            for agg in query_spec["aggregations"]:
                func = getattr(F, agg["function"].lower())
                agg_exprs.append(
                    func(agg["column"]).alias(agg["alias"])
                )
            df = df.agg(*agg_exprs)
        
        # Apply grouping
        if query_spec["group_by"]:
            df = df.groupBy(*query_spec["group_by"])
        
        # Apply ordering
        if query_spec["order_by"]:
            order_exprs = []
            for order in query_spec["order_by"]:
                col = order["column"]
                if order.get("direction", "ASC").upper() == "DESC":
                    col = F.desc(col)
                order_exprs.append(col)
            df = df.orderBy(*order_exprs)
        
        return df
    
    def execute(self,
                connection_type: str,
                database_name: str,
                table_name: str,
                query_spec: Dict,
                update_trigger: bool,
                cache_strategy: str = "NONE",
                config_params: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        config = SparkConfig(
            connection_type=connection_type,
            master="local[*]",  # Default for execution
            app_name="QueryExecutor",
            config_params=config_params or {}
        )
        
        with SessionContext(config) as spark:
            # Get base table
            df = spark.table(f"{database_name}.{table_name}")
            
            # Apply query specification
            result_df = self._apply_query_spec(df, query_spec)
            
            # Apply caching if requested
            if cache_strategy == "MEMORY":
                result_df = result_df.cache()
            elif cache_strategy == "DISK":
                result_df = result_df.persist()
            
            # Create result dataset
            result_dataset = Dataset(
                result_df,
                f"query_result_{database_name}_{table_name}",
                {"query_spec": query_spec}
            )
            
            # Get execution statistics
            stats = {
                "input_rows": df.count(),
                "output_rows": result_df.count(),
                "execution_time": None  # Would require actual timing
            }
            
            return (result_dataset, stats["output_rows"], stats)
