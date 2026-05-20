from typing import Dict, List, Any
from backend.database_manager import DatabaseManager

class OptimizationAnalyzer:
    """Analyzes database schema and suggests optimizations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def analyze_optimizations(self, connection_id: str) -> List[Dict[str, Any]]:
        """Analyze database and suggest optimizations"""
        schemas = self.db_manager.get_all_schemas(connection_id)
        tables = schemas.get("tables", {})
        
        optimizations = []
        
        for table_name, schema in tables.items():
            # Check for missing indexes
            indexes = schema.get("indexes", [])
            foreign_keys = schema.get("foreign_keys", [])
            
            # Check if foreign keys have indexes
            for fk in foreign_keys:
                fk_columns = fk["constrained_columns"]
                has_index = any(
                    set(fk_columns).issubset(set(idx["columns"]))
                    for idx in indexes
                )
                
                if not has_index:
                    optimizations.append({
                        "type": "missing_index",
                        "severity": "high",
                        "table": table_name,
                        "columns": fk_columns,
                        "reason": f"Foreign key columns {fk_columns} should be indexed for better join performance",
                        "suggestion": f"CREATE INDEX idx_{table_name}_{'_'.join(fk_columns)} ON {table_name} ({', '.join(fk_columns)});"
                    })
            
            # Check for tables without primary keys
            if not schema.get("primary_keys"):
                optimizations.append({
                    "type": "missing_primary_key",
                    "severity": "critical",
                    "table": table_name,
                    "reason": "Table lacks a primary key, which is essential for data integrity and performance",
                    "suggestion": f"ALTER TABLE {table_name} ADD COLUMN id SERIAL PRIMARY KEY;"
                })
            
            # Check for large text columns without indexes (if needed for searches)
            columns = schema.get("columns", [])
            for col in columns:
                col_type = str(col["type"]).lower()
                if "text" in col_type or "varchar" in col_type:
                    # Check if column is used in foreign keys (should be indexed)
                    is_fk = any(
                        col["name"] in fk["constrained_columns"]
                        for fk in foreign_keys
                    )
                    if is_fk:
                        continue
                    
                    # This is informational - not all text columns need indexes
                    optimizations.append({
                        "type": "potential_text_index",
                        "severity": "low",
                        "table": table_name,
                        "column": col["name"],
                        "reason": f"Text column '{col['name']}' might benefit from an index if used in WHERE clauses or JOINs",
                        "suggestion": f"Consider creating an index if this column is frequently queried: CREATE INDEX idx_{table_name}_{col['name']} ON {table_name} ({col['name']});"
                    })
            
            # Check for duplicate indexes
            index_columns = {}
            for idx in indexes:
                idx_key = tuple(sorted(idx["columns"]))
                if idx_key in index_columns:
                    optimizations.append({
                        "type": "duplicate_index",
                        "severity": "medium",
                        "table": table_name,
                        "indexes": [index_columns[idx_key], idx["name"]],
                        "reason": f"Duplicate indexes on columns {idx['columns']}",
                        "suggestion": f"Consider dropping one of the duplicate indexes: DROP INDEX {idx['name']};"
                    })
                else:
                    index_columns[idx_key] = idx["name"]
        
        return optimizations
    
    def get_table_optimizations(self, connection_id: str, table_name: str) -> List[Dict[str, Any]]:
        """Get optimization suggestions for a specific table"""
        all_optimizations = self.analyze_optimizations(connection_id)
        return [opt for opt in all_optimizations if opt["table"] == table_name]
