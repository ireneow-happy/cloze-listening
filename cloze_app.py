import streamlit as st
import random
import re

def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            st.warning("Unable to rerun the app. Please update your Streamlit version.")

st.set_page_config(page_title="Cloze Listening Practice", layout="wide")
st.title("🎧 English Cloze Listening Practice App")

# Sidebar for user inputs
st.sidebar.header("Step 1: Input Settings")
paragraph_input = st.sidebar.text_area("Enter paragraphs (one per line):", height=200)
missing_ratio = st.sidebar.slider("Select missing word ratio:", 0.05, 0.9, 0.3, step=0.05)

# Process paragraphs
if paragraph_input:
    paragraphs = [p.strip() for p in paragraph_input.split("\n") if p.strip()]
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
        st.session_state.correct_words = []
        st.session_state.answers = []
        st.session_state.positions = []
        st.session_state.tokens = []
        st.session_state.fill_index = 0

    def generate_cloze_data(paragraph, ratio):
        words = re.findall(r"\b\w+\b|\W", paragraph)
        word_indices = [i for i, w in enumerate(words) if re.match(r"\w+", w)]
        num_to_remove = max(1, int(len(word_indices) * ratio))
        missing_indices = sorted(random.sample(word_indices, num_to_remove))
        answers = [words[i] for i in missing_indices]
        cloze_words = words[:]
        for i in missing_indices:
            cloze_words[i] = "____"
        return cloze_words, answers, missing_indices

    if not st.session_state.tokens:
        tokens, answers, positions = generate_cloze_data(paragraphs[0], missing_ratio)
        st.session_state.tokens = tokens
        st.session_state.answers = answers
        st.session_state.positions = positions
        st.session_state.correct_words = [None] * len(positions)
        st.session_state.fill_index = 0

    current_idx = st.session_state.current_index
    tokens = st.session_state.tokens
    answers = st.session_state.answers
    positions = st.session_state.positions
    correct_words = st.session_state.correct_words
    fill_index = st.session_state.fill_index

    st.subheader(f"Paragraph {current_idx + 1} of {len(paragraphs)}")

    display_tokens = tokens[:]
    for i, pos in enumerate(positions):
        if correct_words[i] is not None:
            display_tokens[pos] = correct_words[i]
    st.write("**Updated Paragraph:**")
    st.write("".join(display_tokens))

    if fill_index < len(positions):
        i = fill_index
        user_input = st.text_input(f"Fill in the blank #{i+1}:", key=f"blank_{i}")
        if user_input and user_input.strip().lower() == answers[i].lower():
            st.session_state.correct_words[i] = answers[i]
            st.session_state.fill_index += 1
            safe_rerun()
    else:
        st.success("All blanks filled correctly!")
        if current_idx + 1 < len(paragraphs):
            if st.button("➡ Next Paragraph"):
                new_tokens, new_answers, new_positions = generate_cloze_data(paragraphs[current_idx + 1], missing_ratio)
                st.session_state.current_index += 1
                st.session_state.tokens = new_tokens
                st.session_state.answers = new_answers
                st.session_state.positions = new_positions
                st.session_state.correct_words = [None] * len(new_positions)
                st.session_state.fill_index = 0
                safe_rerun()
        else:
            st.balloons()
            st.info("🎉 All paragraphs completed!")
