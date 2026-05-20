from typing import Dict, List, Any
from backend.database_manager import DatabaseManager
import networkx as nx

class RelationshipAnalyzer:
    """Analyzes relationships between database tables"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def analyze_relationships(self, connection_id: str) -> Dict[str, Any]:
        """Analyze all relationships in the database"""
        schemas = self.db_manager.get_all_schemas(connection_id)
        tables = schemas.get("tables", {})
        
        relationships = []
        graph = nx.DiGraph()
        
        # Build relationship graph
        for table_name, schema in tables.items():
            graph.add_node(table_name)
            
            for fk in schema.get("foreign_keys", []):
                source_table = table_name
                target_table = fk["referred_table"]
                source_columns = fk["constrained_columns"]
                target_columns = fk["referred_columns"]
                
                relationship = {
                    "source_table": source_table,
                    "target_table": target_table,
                    "source_columns": source_columns,
                    "target_columns": target_columns,
                    "type": "foreign_key"
                }
                relationships.append(relationship)
                
                graph.add_edge(source_table, target_table, 
                             source_columns=source_columns,
                             target_columns=target_columns)
        
        # Find relationship paths
        relationship_paths = self._find_relationship_paths(graph, tables)
        
        # Detect many-to-many relationships
        many_to_many = self._detect_many_to_many(graph, tables)
        
        return {
            "relationships": relationships,
            "graph": graph,
            "relationship_paths": relationship_paths,
            "many_to_many": many_to_many,
            "table_count": len(tables),
            "relationship_count": len(relationships)
        }
    
    def _find_relationship_paths(self, graph: nx.DiGraph, tables: Dict) -> List[List[str]]:
        """Find paths between tables"""
        paths = []
        nodes = list(graph.nodes())
        
        for i, source in enumerate(nodes):
            for target in nodes[i+1:]:
                if nx.has_path(graph, source, target):
                    path = nx.shortest_path(graph, source, target)
                    paths.append(path)
                elif nx.has_path(graph, target, source):
                    path = nx.shortest_path(graph, target, source)
                    paths.append(path)
        
        return paths
    
    def _detect_many_to_many(self, graph: nx.DiGraph, tables: Dict) -> List[Dict[str, Any]]:
        """Detect potential many-to-many relationships"""
        many_to_many = []
        
        # Look for junction tables (tables with multiple foreign keys)
        for table_name, schema in tables.items():
            foreign_keys = schema.get("foreign_keys", [])
            if len(foreign_keys) >= 2:
                # Potential junction table
                referenced_tables = [fk["referred_table"] for fk in foreign_keys]
                many_to_many.append({
                    "junction_table": table_name,
                    "related_tables": referenced_tables,
                    "foreign_keys": foreign_keys
                })
        
        return many_to_many
    
    def get_table_relationships(self, connection_id: str, table_name: str) -> Dict[str, Any]:
        """Get all relationships for a specific table"""
        all_relationships = self.analyze_relationships(connection_id)
        
        table_relationships = {
            "incoming": [],
            "outgoing": []
        }
        
        for rel in all_relationships["relationships"]:
            if rel["source_table"] == table_name:
                table_relationships["outgoing"].append(rel)
            if rel["target_table"] == table_name:
                table_relationships["incoming"].append(rel)
        
        return table_relationships
