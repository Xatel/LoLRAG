# LoLRAG
RAG system for searching LoL champion data

# Setting up docker containers

1. Create `database/postgres-pgvector/.env` with the following keys:
   ```
   DB_HOST=
   DB_PORT=
   DB_NAME=
   DB_USER=
   DB_PASSWORD=
   ```

2. Start the database:
   ```
   docker compose up -d
   ```

# Running the app

1. Create and activate the conda environment:
   ```
   conda env create -f environment.yml
   conda activate lolrag
   ```

2. Start both services:
   ```
   ./start.sh
   ```

   - Chatbot: http://localhost:8000
   - Server:  http://localhost:8888

3. To stop:
   ```
   ./stop.sh
   ```
