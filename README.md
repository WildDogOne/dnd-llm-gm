# LLM Game Master

This is a fork of https://github.com/tegridydev/dnd-llm-game but it starts to feel like more of a total rewrite.

## Features

- **Generate D&D Characters**: Create unique characters with name, race, class, backstory, and items
- **Start New Adventure**: Begin a new adventure with the generated characters
- **Turn-Based Gameplay**: Progress through the adventure with player and Dungeon Master turns

## Requirements

- Python 3.8+
- Haystack
- Streamlit
- Requests
- LangChain
- HuggingFace Transformers
- dotenv
- chromadb

## Installation

1. **Clone the repository**:
    ```
    git clone https://github.com/WildDogOne/dnd-llm-gm.git
    cd dnd-llm-gm
    ```

2. **Create and activate a virtual environment**:
    ``` bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:
    ```
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory with the following content:
    ```plaintext
    LLM_HOST=http://127.0.0.1:11434
    LLM_MODEL=gemma3:latest
    LLM_EMBEDDING_MODEL=embeddinggemma:latest
    PDF_FOLDER=data/pdf
    VECTOR_INDEX_DIR=data/vector_index
    CHROMADB_FOLDER=data/chromadb
    TURN_LIMIT=10
    CHUNK_SIZE=1000
    CHUNK_OVERLAP=50
    PLAYER_COUNT=2
    ```

## Usage

1. **Start Ollama**:
    ```
    ollama serve
    ```

2. **Run the Streamlit app**:
    ```
    streamlit run ui/streamlit_app.py
    ```

3. **Access the app**:
   Open your browser and go to `http://localhost:8501`.

## How to Play

1. Generate a new party.
2. Start a new adventure.
3. Play the next turn.

May your dice roll high!

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request!


