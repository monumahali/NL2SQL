from openai import OpenAI
from typing import Dict, Any, Optional, List
from backend.config import settings
from backend.database_manager import DatabaseManager
import json

class LLMQueryGenerator:
    """Generates SQL queries from natural language using OpenAI"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        api_key = settings.openai_api_key or ""
        if not api_key:
            # Allow initialization without API key - will fail gracefully when used
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Latest OpenAI model
    
    def generate_query(self, connection_id: str, natural_language_query: str) -> Dict[str, Any]:
        """Generate SQL query from natural language"""
        if not self.client:
            return {
                "query": "",
                "natural_language": natural_language_query,
                "success": False,
                "error": "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file."
            }
        try:
            # Get database schema
            schemas = self.db_manager.get_all_schemas(connection_id)
            tables = schemas.get("tables", {})
            views = schemas.get("views", [])
            
            # Build schema context
            schema_context = self._build_schema_context(tables, views)
            
            # Create prompt for OpenAI
            prompt = self._create_prompt(natural_language_query, schema_context)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a SQL expert. Generate accurate SQL queries based on natural language requests and database schemas. Always return valid SQL that follows best practices."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up SQL query (remove markdown code blocks if present)
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            sql_query = sql_query.strip()
            
            return {
                "query": sql_query,
                "natural_language": natural_language_query,
                "success": True
            }
        
        except Exception as e:
            return {
                "query": "",
                "natural_language": natural_language_query,
                "success": False,
                "error": str(e)
            }
    
    def _build_schema_context(self, tables: Dict, views: List[str]) -> str:
        """Build schema context string for LLM"""
        context = "Database Schema:\n\n"
        
        for table_name, schema in tables.items():
            context += f"Table: {table_name}\n"
            context += "Columns:\n"
            
            for col in schema.get("columns", []):
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                context += f"  - {col['name']}: {col['type']} {nullable}\n"
            
            if schema.get("primary_keys"):
                context += f"Primary Keys: {', '.join(schema['primary_keys'])}\n"
            
            if schema.get("foreign_keys"):
                context += "Foreign Keys:\n"
                for fk in schema["foreign_keys"]:
                    context += f"  - {fk['constrained_columns']} -> {fk['referred_table']}({fk['referred_columns']})\n"
            
            if schema.get("indexes"):
                context += "Indexes:\n"
                for idx in schema["indexes"]:
                    unique = "UNIQUE" if idx["unique"] else ""
                    context += f"  - {idx['name']}: {', '.join(idx['columns'])} {unique}\n"
            
            context += "\n"
        
        if views:
            context += f"Views: {', '.join(views)}\n"
        
        return context
    
    def _create_prompt(self, natural_language_query: str, schema_context: str) -> str:
        """Create prompt for OpenAI"""
        return f"""Based on the following database schema, generate a SQL query for this request:

{schema_context}

User Request: {natural_language_query}

Generate a SQL query that fulfills this request. Only return the SQL query, no explanations unless the request is ambiguous or impossible to fulfill."""

    def explain_query(self, query: str) -> str:
        """Explain what a SQL query does in natural language"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a SQL expert. Explain SQL queries in clear, natural language."
                    },
                    {
                        "role": "user",
                        "content": f"Explain what this SQL query does:\n\n{query}"
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Error explaining query: {str(e)}"
