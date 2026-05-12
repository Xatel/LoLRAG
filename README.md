# LoLRAG
RAG system for searching LoL champion data

# Setting up docker containers

1. Create `database/postgres-pgvector/.env` with the following keys:
   ```
   POSTGRES_USER=
   POSTGRES_PASSWORD=
   POSTGRES_DB=
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
