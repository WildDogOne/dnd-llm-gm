# LLM Game Master

This is a fork of https://github.com/tegridydev/dnd-llm-game but it starts to feel like more of a total rewrite.

## Features

- **Generate D&D Characters**: Create unique characters with name, race, class, backstory, and items
- **Start New Adventure**: Begin a new adventure with the generated characters
- **Turn-Based Gameplay**: Progress through the adventure with player and Dungeon Master turns

## TODOs
- Add Tools
  - Dice Rolling
  - Shopping
  - Character Management

## Requirements

- streamlit~=1.51.0
- ollama~=0.6.0
- haystack-ai~=2.19.0
- datasets~=4.4.1
- sentence-transformers~=
- ollama-haystack~=5.3.0
- chroma-haystack~=3.4.0
- jsonschema~=4.25.1
- pydantic-settings~=2.11.0
- pydantic~=2.12.4 - pypdf~=6.1.3

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
1. (Optional) Upload PDF(s) of the adventure you want to play
1. Start a new adventure. (Or write your own intro)
1. Play

May your dice roll high!

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request!


