# Monu changed the README.md
# Added Feature
# To pull doing some changes

# SQL Query Writer

A comprehensive database analysis and query tool that allows you to connect to any database, explore schemas, analyze relationships, get optimization suggestions, and generate SQL queries using natural language powered by OpenAI.

## Features

* 🔌 **Multi-Database Support**: Connect to PostgreSQL, MySQL, SQLite, and Neon DB
* 🔍 **Schema Exploration**: View all tables, views, columns, indexes, and constraints
* 🔗 **Relationship Analysis**: Visualize and understand relationships between tables
* ⚡ **Optimization Suggestions**: Get recommendations for improving database performance
* 💬 **Natural Language to SQL**: Generate SQL queries from natural language using OpenAI GPT-4
* 📊 **Query Execution**: Execute and visualize query results
* 🎨 **Modern UI**: Beautiful Streamlit interface for easy interaction

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd sqlwuerywriter
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory:

```
OPENAI\_API\_KEY=your\_openai\_api\_key\_here
```

## Usage

### Starting the Backend (FastAPI)

1. Start the FastAPI server:

```bash
cd backend
python api.py
```

Or using uvicorn directly:

```bash
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Starting the Frontend (Streamlit)

1. In a new terminal, start the Streamlit app:

```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

### Connecting to a Database

1. Use the sidebar to select your database type
2. Enter connection details:

   * **PostgreSQL/MySQL**: Host, port, database name, username, password
   * **SQLite**: Path to database file
   * **Neon DB**: Connection string
3. Click "Connect"

### Using Natural Language Queries

1. Navigate to the "Query Chat" tab
2. Type your question in natural language (e.g., "Show me all users who registered in the last month")
3. The system will generate a SQL query
4. Review and execute the query

## Project Structure

```
sqlwuerywriter/
├── backend/
│   ├── \_\_init\_\_.py
│   ├── api.py                 # FastAPI application
│   ├── config.py              # Configuration settings
│   ├── database\_manager.py    # Database connection and management
│   ├── relationship\_analyzer.py  # Table relationship analysis
│   ├── optimization\_analyzer.py  # Optimization suggestions
│   └── llm\_query\_generator.py   # OpenAI integration for NL to SQL
├── app.py                     # Streamlit frontend
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
└── README.md                  # This file
```

## API Endpoints

### Connection Management

* `POST /connect` - Connect to a database
* `POST /disconnect/{connection\_id}` - Disconnect from a database

### Database Information

* `GET /database/info/{connection\_id}` - Get comprehensive database info
* `GET /database/schemas/{connection\_id}` - Get all schemas
* `GET /database/tables/{connection\_id}` - Get all tables
* `GET /database/views/{connection\_id}` - Get all views
* `GET /database/table/{connection\_id}/{table\_name}` - Get table schema

### Analysis

* `GET /database/relationships/{connection\_id}` - Analyze table relationships
* `GET /database/optimizations/{connection\_id}` - Get optimization suggestions

### Query Execution

* `POST /query/execute` - Execute a SQL query
* `POST /query/generate` - Generate SQL from natural language
* `POST /query/explain` - Explain a SQL query

## Technologies Used

* **Backend**: FastAPI, SQLAlchemy, OpenAI API
* **Frontend**: Streamlit
* **Database Support**: PostgreSQL, MySQL, SQLite, Neon DB
* **Visualization**: Plotly, NetworkX
* **LLM**: OpenAI GPT-4 Turbo

## Requirements

* Python 3.8+
* OpenAI API key
* Database access credentials

## Notes

* Make sure the FastAPI backend is running before using the Streamlit frontend
* The OpenAI API key is required for natural language query generation
* Database connections are managed per session
* All queries are executed with read-only access (no modifications to schema)

## License

MIT License

