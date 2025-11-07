import logging, re, os, pickle
from .settings import settings
from services.chromadb_client import chromadb_client
logger = logging.getLogger(__name__)

game_state_file = settings.game_state / "game_state.pkl"
party_file = settings.game_state / "party_state.pkl"

def save_game_state(game_state=None, party=None):
    game_state_file.parent.mkdir(parents=True, exist_ok=True)
    party_file.parent.mkdir(parents=True, exist_ok=True)
    if game_state:
        with open(game_state_file, 'wb') as f:
            pickle.dump(game_state, f)
    if party:
        with open(party_file, 'wb') as f:
            pickle.dump(party, f)


def load_game_state(file=None):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return pickle.load(f)
    return None


def delete_game_state():
    chromadb_client.reset_store()
    if os.path.exists(game_state_file):
        os.remove(game_state_file)
    if os.path.exists(party_file):
        os.remove(party_file)


# ——— Context utilities —————————————————————————————————

def last_sentences(text: str, n: int) -> str:
    """
    Grab the last n sentences (naïve split) for context truncation.
    """
    sentences = re.split(r'(?<=[\.!?])\s+', text.strip())
    return " ".join(sentences[-n:])
