import os, sys, logging, pickle
# import torch;
from pathlib import Path

# torch.classes.__path__ = []  # avoid Streamlit watcher errors

import streamlit as st
import time

# ensure project root
sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..")))

from core.settings import settings
from services.game_runner import GameRunner
# from core.utils import build_index
from services.chromadb_client import chromadb_client

logger = logging.getLogger(__name__)
st.set_page_config(page_title="AI Game Master", layout="wide")
# Create an empty placeholder for the info message
info_placeholder = st.empty()
from core.utils import save_game_state, load_game_state, delete_game_state, game_state_file, party_file


def display_party(party):
    st.subheader("🧙‍♂️ Party Sheet")
    cols = st.columns(len(party))
    for col, (name, char) in zip(cols, party.items()):
        with col.expander(name, expanded=False):
            data = char.model_dump()
            st.write(f"**Name:** {data['name']}  ")
            st.write(f"**Race:** {data['race']}  ")
            st.write(f"**Class:** {data['character_class']}  ")
            st.write("**Items:**")
            x = ""
            for it in data["items"]:
                x += f"- {it}\n"
            st.markdown(x)
            st.write("**Backstory (snippet):**")
            st.write(data["backstory"][:200] + "...")


def display_log(story):
    st.subheader("📜 Adventure Log")
    embedding_list = []
    for i, line in enumerate(story, start=1):
        if ":" in line:
            who, text = line.split(":", 1)
            embedding_list.append(f"{who} : {text}")
            icon = "🧙‍♂️" if who.strip() == "DM" else "🎲"
            with st.expander(f"Turn {i} - {icon}"):
                st.markdown(f"**{who}:** {text.strip()}")
        else:
            st.error(f"Invalid log entry at turn {i}: \n{line}")


def main():
    # init runner
    if "runner" not in st.session_state:
        st.session_state.runner = GameRunner()
    runner: GameRunner = st.session_state.runner
    gs = runner.state
    if "loaded" not in st.session_state:
        st.session_state.loaded = False
        if os.path.exists(game_state_file):
            gs = load_game_state(game_state_file)
            runner.state = gs
        if os.path.exists(party_file) and not runner.party:
            runner.party = load_game_state(party_file)
        st.session_state.loaded = True

    ## Sidebar
    # Create a question bar that is always present
    st.sidebar.title("Ask DM")
    question = st.sidebar.chat_input("Enter your question:")
    if question:
        result = runner.ask_dm(question)
        st.sidebar.markdown(result)
    with st.sidebar.expander("Settings"):
        st.markdown(f"- **Ollama Host:** `{settings.llm_host}`\n"
                    f"- **Model:** `{settings.llm_model}`\n"
                    f"- **Turn Limit:** {settings.turn_limit}\n"
                    f"- **RAG:** {settings.enable_rag}")
        # Two colum layout for the load and save buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button('Save Game State'):
                save_game_state(game_state=gs)
                if runner.party:
                    save_game_state(party=runner.party)
        with col2:
            if st.button('Delete Game State'):
                delete_game_state()
                st.write("Game state deleted.")
    with st.sidebar.expander("PDF"):
        # RAG PDF upload
        up = st.file_uploader("Upload PDFs for lore", accept_multiple_files=True, type="pdf")
        if up:
            with st.spinner("Building Index", show_time=True):
                # time.sleep(5)
                for f in up:
                    dst = settings.pdf_folder / f.name
                    dst.write_bytes(f.getbuffer())
                    chromadb_client.embed_pdf(dst)
            st.success("PDF index built!")

    st.title("🗡️ Virtual Game Master")

    # Phase: start → new party
    if gs.phase == "start":
        if st.button("Generate Party"):
            try:
                with info_placeholder.container():
                    st.info("Generating Party...")
                runner.new_party()

                with info_placeholder.container():
                    st.success("Party Generated")
                save_game_state(game_state=gs)
                if runner.party:
                    save_game_state(party=runner.party)
            except Exception as e:
                st.error(e)
        # return  # re-render

    # Show party once generated
    if runner.party:
        display_party(runner.party)

    # Phase: ready to start
    if gs.phase == "start" and runner.party:
        if st.button("🐉 Start Adventure"):
            try:
                runner.start_adventure()
                save_game_state(game_state=gs)
                if runner.party:
                    save_game_state(party=runner.party)
            except Exception as e:
                st.error(e)

    # Phase: intro text
    if gs.phase == "intro":
        st.markdown(f"**Intro:** {gs.intro_text}")
        if st.button("▶️ Continue"):
            runner.request_options()
            save_game_state(game_state=gs)
            if runner.party:
                save_game_state(party=runner.party)

    # Phase: choice
    if gs.phase == "choice":
        opts = gs.current_options
        with st.form(key=f"form_{gs.turn}", clear_on_submit=False):
            choice = st.radio("What will you do?", opts, key=f"choice_{gs.turn}")
            custom_text = st.text_input("Or enter your own action:", key=f"custom_text_{gs.turn}")
            submit = st.form_submit_button("Submit Choice")
        if submit:
            if custom_text or choice:
                if custom_text:
                    runner.process_player_choice(text=custom_text)
                elif choice:
                    runner.process_player_choice(idx=opts.index(choice))
                runner.run_dm_turn()
            else:
                with info_placeholder.container():
                    st.info("Select an option or write a custom text")
            save_game_state(game_state=gs)
            if runner.party:
                save_game_state(party=runner.party)

    # Phase: DM response shown (and loop back to options)
    if gs.phase == "dm_response":
        last = gs.story[-1]
        who, txt = last.split(":", 1)
        st.markdown(f"**{who.strip()}:** {txt.strip()}")
        if st.button("▶️ Next Turn"):
            runner.request_options()
            save_game_state(game_state=gs)
            if runner.party:
                save_game_state(party=runner.party)
        # fall through to log

    # Always show log at end
    display_log(gs.story)


if __name__ == "__main__":
    main()
