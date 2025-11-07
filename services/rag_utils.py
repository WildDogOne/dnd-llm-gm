import json
import logging
import re
from typing import Dict, List

from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed

from core.utils import last_sentences
from services.ollama_client import ollama_client
from core.settings import settings
from .chromadb_client import chromadb_client
from haystack.dataclasses import ChatMessage

logger = logging.getLogger(__name__)


# ——— Character schema ——————————————————————————————————

class Character(BaseModel):
    name: str
    race: str
    character_class: str = Field(..., alias="class")
    backstory: str
    items: List[str]
    personality: str

    model_config = {"populate_by_name": True}


# ——— JSON extraction ——————————————————————————————————

def _extract_json(raw: str) -> str:
    # Strip fences (case-insensitive), then grab first {...} non-greedily
    cleaned = re.sub(r"```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    m = re.search(r"\{.*?\}", cleaned, flags=re.DOTALL)
    return m.group(0) if m else cleaned


# ——— Generation params ——————————————————————————————————

CHAR_PROMPT = "You are a D&D character creator.  Output exactly one JSON object with keys: name, race, class, backstory, items, personality."
CHAR_MAX = 200
CHAR_TEMP = 0.7

DM_INTRO_PROMPT = (
    "SYSTEM: You are the Dungeon Master. "
    "Describe a scene (200–300 words) and end with a clear challenge.\n"
    "USER: Start an epic adventure with: {names}."
)
DM_TURN_PROMPT = (
    "SYSTEM: You are the Dungeon Master. Continue the narrative (150–250 words), "
    "summarizing what happened and presenting the next challenge.\n"
    "USER: {context}"
)

DM_MAX = 3000
DM_TEMP = 0.8

PLAYER_PROMPT = (
    "SYSTEM: You are a player character. Stay in character, describe only your single action (100–150 words).\n"
    "USER: {context}"
)
PLAYER_MAX = 150
PLAYER_TEMP = 0.6


def dm_question_prompt(question: str = None, context: str = None) -> dict:
    return [
        ChatMessage.from_system(
            "\nSYSTEM: You are the Dungeon Master. You answer your players questions truthfully without giving away too much information."),
        ChatMessage.from_user(
            f"Player Question {question}\nContext: {context}")
    ]


def create_options_prompt(context):
    return [
        {'role': 'system',
         'content': "You are the Dungeon Master."},
        {'role': 'user',
         'content': f"Given recent events, output exactly 3 possible action options as a JSON array.\n{context}"}
    ]
    # Haystack Prompt
    """
        return [
            ChatMessage.from_system("\nYou are the Dungeon Master."),
            ChatMessage.from_user(
                f"Given recent events, output exactly 3 possible action options as a JSON array.\n{context}")
        ]
    """


OPTIONS_MAX = 150
OPTIONS_TEMP = 0.6


# ——— Character generation with retry ——————————————————————

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
def generate_character_sync() -> Character:
    class Char(BaseModel):
        name: str
        race: str
        character_class: str
        backstory: str
        items: list[str]
        personality: str

    # messages = [ChatMessage.from_user("CHAR_PROMPT")]
    messages = [{'role': 'user', 'content': CHAR_PROMPT}]
    js = ollama_client.structured(
        messages=messages,
        options={"temperature": CHAR_TEMP},
        output_format=Char.model_json_schema(),
    )

    try:
        data = json.loads(js)
        return Character.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning("Parse error (retrying): %s\nRaw: %s", e, js)
        raise


def generate_party_sync() -> Dict[str, Character]:
    return {f"Player {i + 1}": generate_character_sync() for i in range(settings.player_count)}


def start_adventure_sync(party: Dict[str, Character]) -> str:
    names = ", ".join(party.keys())
    prompt = DM_INTRO_PROMPT.format(names=names)
    return ollama_client.generate(
        prompt=prompt,
        max_tokens=DM_MAX,
        temperature=DM_TEMP
    )


def player_turn_sync(state: Dict, name: str, info: Character) -> str:
    recent = last_sentences(" ".join(state["story"]), 10)
    # lore = retrieve(info.backstory + " " + recent)
    lore = chromadb_client.retrieve(info.backstory + " " + recent)
    if lore:
        ctxt = f"Character: {info.model_dump_json()}\nRecent: {recent}\nAdditional Backstory: {' | '.join(lore)}"
    else:
        ctxt = f"Character: {info.model_dump_json()}\nRecent: {recent}"
    prompt = PLAYER_PROMPT.format(context=ctxt)
    return ollama_client.generate(prompt=prompt, max_tokens=PLAYER_MAX, temperature=PLAYER_TEMP)


def ask_dm_sync(state: Dict, question: str) -> str:
    recent = last_sentences(" ".join(state["story"]), 10)
    lore = chromadb_client.retrieve(recent)
    if lore:
        ctxt = f"Recent events: {recent}\nAdditional Backstory: {' | '.join(lore)}"
    else:
        ctxt = f"Recent events: {recent}"
    prompt = dm_question_prompt(question=question, context=ctxt)
    answer = ollama_client.chat(messages=prompt, options={"max_tokens": 2000, "temperature": 0.8})
    return answer


def dm_turn_sync(state: Dict) -> str:
    recent = last_sentences(" ".join(state["story"]), 10)
    # lore = retrieve(recent)
    # ollama_client.client.generate(prompt=f{})
    lore = chromadb_client.retrieve(recent)
    if lore:
        ctxt = f"Recent events: {recent}\nAdditional Backstory: {' | '.join(lore)}"
    else:
        ctxt = f"Recent events: {recent}"
    prompt = DM_TURN_PROMPT.format(context=ctxt)
    return ollama_client.generate(prompt=prompt, max_tokens=DM_MAX, temperature=DM_TEMP)


def generate_options_sync(state: Dict) -> List[str]:
    class Choices(BaseModel):
        choice: list[str]

    recent = last_sentences(" ".join(state["story"]), 10)
    ctxt = f"Recent events: {recent}"
    prompt = create_options_prompt(ctxt)

    js = ollama_client.structured(
        messages=prompt, output_format=Choices.model_json_schema()
    )

    try:
        opts = json.loads(js)
    except Exception:
        logger.error("Options parse error, raw: %s", js)
    return opts["choice"]
    # return ["Continue forward", "Inspect surroundings", "Rest and recover"]
