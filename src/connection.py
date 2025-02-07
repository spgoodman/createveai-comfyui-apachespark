import os
from typing import Optional, Dict, Any
import json
from pathlib import Path
from pyspark.sql import SparkSession
from dataclasses import asdict

from .base import SparkConfig, DatabricksConfig, ValidationError

class SparkConnectionManager:
    """Manages Spark connections and sessions"""
    
    _instance = None
    _active_session = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SparkConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.config_path = Path(os.path.expanduser("~/.createveai/spark_config.json"))
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.config = json.load(f)
        else:
            self.config = {
                "local": {
                    "master": "local[*]",
                    "app_name": "CreateveAI",
                    "config_params": {
                        "spark.driver.memory": "4g",
                        "spark.sql.execution.arrow.enabled": "true"
                    }
                },
                "databricks": {}
            }
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_config()
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_session(self, config: SparkConfig) -> SparkSession:
        """Get or create a Spark session"""
        if self._active_session:
            return self._active_session
        
        if config.connection_type.upper() == "LOCAL":
            builder = (SparkSession.builder
                      .master(config.master)
                      .appName(config.app_name))
            
            # Apply configuration parameters
            for key, value in config.config_params.items():
                builder = builder.config(key, value)
            
            self._active_session = builder.getOrCreate()
            
        elif config.connection_type.upper() == "DATABRICKS":
            # Validate Databricks configuration
            databricks_config = self.config.get("databricks", {})
            if not databricks_config:
                raise ValidationError("Databricks configuration not found")
            
            # Set up Databricks-specific configuration
            os.environ["DATABRICKS_HOST"] = databricks_config["workspace_url"]
            os.environ["DATABRICKS_TOKEN"] = databricks_config["token"]
            
            builder = (SparkSession.builder
                      .master("databricks")
                      .appName(config.app_name))
            
            # Apply Databricks-specific configs
            for key, value in config.config_params.items():
                builder = builder.config(key, value)
            
            self._active_session = builder.getOrCreate()
            
        else:
            raise ValidationError(f"Unknown connection type: {config.connection_type}")
        
        return self._active_session
    
    def stop_session(self):
        """Stop the current Spark session"""
        if self._active_session:
            self._active_session.stop()
            self._active_session = None
    
    def update_databricks_config(self, config: DatabricksConfig):
        """Update Databricks configuration"""
        self.config["databricks"] = asdict(config)
        self._save_config()
    
    def update_local_config(self, config: SparkConfig):
        """Update local Spark configuration"""
        if config.connection_type.upper() != "LOCAL":
            raise ValidationError("Configuration must be for local connection")
        
        self.config["local"] = {
            "master": config.master,
            "app_name": config.app_name,
            "config_params": config.config_params
        }
        self._save_config()

class SessionContext:
    """Context manager for Spark sessions"""
    
    def __init__(self, config: SparkConfig):
        self.config = config
        self.manager = SparkConnectionManager()
    
    def __enter__(self) -> SparkSession:
        return self.manager.get_session(self.config)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Log the error but don't stop the session
            print(f"Error in Spark session: {exc_val}")
        # Don't stop the session here - it will be reused
        pass

def get_spark_session(config: SparkConfig) -> SparkSession:
    """Utility function to get a Spark session"""
    return SparkConnectionManager().get_session(config)
