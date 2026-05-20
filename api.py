from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import pandas as pd
from backend.database_manager import DatabaseManager
from backend.relationship_analyzer import RelationshipAnalyzer
from backend.optimization_analyzer import OptimizationAnalyzer
from backend.llm_query_generator import LLMQueryGenerator

app = FastAPI(title="SQL Query Writer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_manager = DatabaseManager()
relationship_analyzer = RelationshipAnalyzer(db_manager)
optimization_analyzer = OptimizationAnalyzer(db_manager)

try:
    llm_generator = LLMQueryGenerator(db_manager)
except Exception as e:
    print(f"Warning: LLM generator initialization failed: {e}")
    llm_generator = None

class DatabaseConnection(BaseModel):
    connection_id: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None
    connection_string: Optional[str] = None

class QueryRequest(BaseModel):
    connection_id: str
    query: str

class NaturalLanguageQuery(BaseModel):
    connection_id: str
    query: str

class ExplainQueryRequest(BaseModel):
    query: str

@app.get("/")
def root():
    return {"message": "SQL Query Writer API"}

@app.post("/connect")
def connect_database(connection: DatabaseConnection):
    try:
        success = db_manager.connect(
            connection.connection_id,
            connection.db_type,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=connection.password,
            path=connection.path,
            connection_string=connection.connection_string
        )
        if success:
            return {"success": True, "message": "Connected successfully"}
        else:
            raise HTTPException(status_code=400, detail="Connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/disconnect/{connection_id}")
def disconnect_database(connection_id: str):
    try:
        db_manager.disconnect(connection_id)
        return {"success": True, "message": "Disconnected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/info/{connection_id}")
def get_database_info(connection_id: str):
    try:
        info = db_manager.get_database_info(connection_id)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/schemas/{connection_id}")
def get_all_schemas(connection_id: str):
    try:
        schemas = db_manager.get_all_schemas(connection_id)
        if not schemas:
            return {"tables": {}, "views": [], "table_names": []}
        return schemas
    except Exception as e:
        print(f"Error getting schemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/tables/{connection_id}")
def get_tables(connection_id: str):
    try:
        tables = db_manager.get_all_tables(connection_id)
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/views/{connection_id}")
def get_views(connection_id: str):
    try:
        views = db_manager.get_all_views(connection_id)
        return {"views": views}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/table/{connection_id}/{table_name}")
def get_table_schema(connection_id: str, table_name: str):
    try:
        schema = db_manager.get_table_schema(connection_id, table_name)
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/relationships/{connection_id}")
def get_relationships(connection_id: str):
    try:
        relationships = relationship_analyzer.analyze_relationships(connection_id)
        graph_data = {
            "nodes": list(relationships["graph"].nodes()),
            "edges": [
                {
                    "source": edge[0],
                    "target": edge[1],
                    "source_columns": relationships["graph"].edges[edge].get("source_columns", []),
                    "target_columns": relationships["graph"].edges[edge].get("target_columns", [])
                }
                for edge in relationships["graph"].edges()
            ]
        }
        return {
            "relationships": relationships["relationships"],
            "graph": graph_data,
            "relationship_paths": relationships["relationship_paths"],
            "many_to_many": relationships["many_to_many"],
            "table_count": relationships["table_count"],
            "relationship_count": relationships["relationship_count"]
        }
    except Exception as e:
        print(f"Error getting relationships: {e}")
        # Return empty data instead of error
        return {
            "relationships": [],
            "graph": {"nodes": [], "edges": []},
            "relationship_paths": [],
            "many_to_many": [],
            "table_count": 0,
            "relationship_count": 0
        }

@app.get("/database/optimizations/{connection_id}")
def get_optimizations(connection_id: str):
    try:
        optimizations = optimization_analyzer.analyze_optimizations(connection_id)
        return {"optimizations": optimizations}
    except Exception as e:
        print(f"Error getting optimizations: {e}")
        return {"optimizations": []}

@app.post("/query/execute")
def execute_query(request: QueryRequest):
    try:
        df = db_manager.execute_query(request.connection_id, request.query)
        return {
            "success": True,
            "data": df.to_dict(orient="records"),
            "columns": list(df.columns),
            "row_count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/generate")
def generate_query(request: NaturalLanguageQuery):
    try:
        if llm_generator is None:
            raise HTTPException(status_code=503, detail="LLM service not available")
        result = llm_generator.generate_query(request.connection_id, request.query)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/explain")
def explain_query(request: ExplainQueryRequest):
    try:
        if llm_generator is None:
            raise HTTPException(status_code=503, detail="LLM service not available")
        explanation = llm_generator.explain_query(request.query)
        return {"explanation": explanation}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
