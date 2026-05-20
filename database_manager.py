from sqlalchemy import create_engine, inspect, text, MetaData, Table
from sqlalchemy.engine import Engine
from typing import Dict, List, Optional, Any
import pandas as pd
from urllib.parse import quote_plus

class DatabaseManager:
    """Manages connections to various database types"""
    
    def __init__(self):
        self.engines: Dict[str, Engine] = {}
        self.connections: Dict[str, Any] = {}
    
    def get_connection_string(self, db_type: str, **kwargs) -> str:
        """Generate connection string based on database type"""
        if db_type.lower() == "postgresql" or db_type.lower() == "neon":
            # Support both PostgreSQL and Neon DB
            # If connection_string is provided, use it directly (common for Neon DB)
            if kwargs.get("connection_string"):
                return kwargs["connection_string"]
            
            # Otherwise, build from individual components
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 5432)
            database = kwargs.get("database", "postgres")
            username = kwargs.get("username", "postgres")
            password = kwargs.get("password", "")
            
            return f"postgresql://{username}:{quote_plus(password)}@{host}:{port}/{database}"
        
        elif db_type.lower() == "mysql":
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 3306)
            database = kwargs.get("database", "mysql")
            username = kwargs.get("username", "root")
            password = kwargs.get("password", "")
            return f"mysql+pymysql://{username}:{quote_plus(password)}@{host}:{port}/{database}"
        
        elif db_type.lower() == "sqlite":
            path = kwargs.get("path", "database.db")
            return f"sqlite:///{path}"
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def connect(self, connection_id: str, db_type: str, **kwargs) -> bool:
        """Establish connection to database"""
        try:
            connection_string = self.get_connection_string(db_type, **kwargs)
            engine = create_engine(connection_string, echo=False)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.engines[connection_id] = engine
            return True
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False
    
    def disconnect(self, connection_id: str):
        """Close database connection"""
        if connection_id in self.engines:
            self.engines[connection_id].dispose()
            del self.engines[connection_id]
        if connection_id in self.connections:
            del self.connections[connection_id]
    
    def get_engine(self, connection_id: str) -> Optional[Engine]:
        """Get database engine for connection"""
        return self.engines.get(connection_id)
    
    def get_all_tables(self, connection_id: str) -> List[str]:
        """Get list of all tables in database"""
        engine = self.get_engine(connection_id)
        if not engine:
            return []
        
        inspector = inspect(engine)
        # Get all schemas and collect tables from each
        tables = []
        try:
            # Try to get schemas (PostgreSQL/Neon)
            schemas = inspector.get_schema_names()
            for schema in schemas:
                # Skip system schemas
                if schema not in ['information_schema', 'pg_catalog', 'pg_toast']:
                    schema_tables = inspector.get_table_names(schema=schema)
                    for table in schema_tables:
                        if schema == 'public':
                            tables.append(table)
                        else:
                            tables.append(f"{schema}.{table}")
        except:
            # Fallback for databases without schema support
            tables = inspector.get_table_names()
        
        return tables
    
    def get_all_views(self, connection_id: str) -> List[str]:
        """Get list of all views in database"""
        engine = self.get_engine(connection_id)
        if not engine:
            return []
        
        inspector = inspect(engine)
        # Get all schemas and collect views from each
        views = []
        try:
            schemas = inspector.get_schema_names()
            for schema in schemas:
                if schema not in ['information_schema', 'pg_catalog', 'pg_toast']:
                    schema_views = inspector.get_view_names(schema=schema)
                    for view in schema_views:
                        if schema == 'public':
                            views.append(view)
                        else:
                            views.append(f"{schema}.{view}")
        except:
            views = inspector.get_view_names()
        
        return views
    
    def get_table_schema(self, connection_id: str, table_name: str) -> Dict[str, Any]:
        """Get detailed schema information for a table"""
        engine = self.get_engine(connection_id)
        if not engine:
            return {}
        
        inspector = inspect(engine)
        
        # Handle schema.table format
        schema = 'public'  # Default to public schema for PostgreSQL
        if '.' in table_name:
            schema, table_name = table_name.split('.', 1)
        
        try:
            columns = inspector.get_columns(table_name, schema=schema)
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
            primary_keys = pk_constraint.get('constrained_columns', []) if pk_constraint else []
            foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
            indexes = inspector.get_indexes(table_name, schema=schema)
        except Exception as e:
            print(f"Error getting schema for {table_name}: {e}")
            # Fallback without schema
            try:
                columns = inspector.get_columns(table_name)
                pk_constraint = inspector.get_pk_constraint(table_name)
                primary_keys = pk_constraint.get('constrained_columns', []) if pk_constraint else []
                foreign_keys = inspector.get_foreign_keys(table_name)
                indexes = inspector.get_indexes(table_name)
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                return {"columns": [], "primary_keys": [], "foreign_keys": [], "indexes": []}
        
        return {
            "columns": [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": str(col.get("default", "")),
                    "autoincrement": col.get("autoincrement", False)
                }
                for col in columns
            ],
            "primary_keys": primary_keys,
            "foreign_keys": [
                {
                    "constrained_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"]
                }
                for fk in foreign_keys
            ],
            "indexes": [
                {
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx.get("unique", False)
                }
                for idx in indexes
            ]
        }
    
    def get_all_schemas(self, connection_id: str) -> Dict[str, Any]:
        """Get complete schema information for all tables"""
        tables = self.get_all_tables(connection_id)
        views = self.get_all_views(connection_id)
        
        schemas = {}
        for table in tables:
            schemas[table] = self.get_table_schema(connection_id, table)
        
        return {
            "tables": schemas,
            "views": views,
            "table_names": tables
        }
    
    def execute_query(self, connection_id: str, query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        engine = self.get_engine(connection_id)
        if not engine:
            raise ValueError("No active connection")
        
        return pd.read_sql_query(text(query), engine)
    
    def get_database_info(self, connection_id: str) -> Dict[str, Any]:
        """Get comprehensive database information"""
        engine = self.get_engine(connection_id)
        if not engine:
            return {}
        
        inspector = inspect(engine)
        
        return {
            "database_name": inspector.default_schema_name if hasattr(inspector, 'default_schema_name') else "default",
            "tables": self.get_all_tables(connection_id),
            "views": self.get_all_views(connection_id),
            "schemas": self.get_all_schemas(connection_id)
        }
