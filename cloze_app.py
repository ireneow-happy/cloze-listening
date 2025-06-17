
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

# Sidebar input
st.sidebar.header("Step 1: Input Settings")
paragraph_input = st.sidebar.text_area("Enter paragraphs (one per line):", height=200)
missing_ratio = st.sidebar.slider("Select missing word ratio:", 0.05, 0.9, 0.3, step=0.05)
start_button = st.sidebar.button("✅ Generate Cloze Paragraphs")

# Storage initialization
if "initialized" not in st.session_state:
    st.session_state.initialized = False

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

# Trigger generation only after pressing button
if start_button and paragraph_input:
    paragraphs = [p.strip() for p in paragraph_input.split("\n") if p.strip()]
    tokens, answers, positions = generate_cloze_data(paragraphs[0], missing_ratio)
    st.session_state.tokens = tokens
    st.session_state.answers = answers
    st.session_state.positions = positions
    st.session_state.correct_words = [None] * len(positions)
    st.session_state.fill_index = 0
    st.session_state.total_missing = len(positions)
    st.session_state.initialized = True
    st.session_state.feedback_message = ""

if st.session_state.initialized:
    tokens = st.session_state.tokens
    answers = st.session_state.answers
    positions = st.session_state.positions
    correct_words = st.session_state.correct_words
    fill_index = st.session_state.fill_index
    total = st.session_state.total_missing

    st.subheader(f"Paragraph 1 of 1")
    st.markdown(f"🟢 **Progress: {sum(w is not None for w in correct_words)} / {total}**")

    # Render paragraph with correct answers marked
    display_tokens = tokens[:]
    for i, pos in enumerate(positions):
        if correct_words[i] is not None:
            display_tokens[pos] = f"<u><b>{correct_words[i]}</b> ✅</u>"
    st.markdown("**Updated Paragraph:**", unsafe_allow_html=True)
    st.markdown("".join(display_tokens), unsafe_allow_html=True)

    # Input next word
    if fill_index < total:
        user_input = st.text_input(f"Fill in the blank #{fill_index+1}:", key=f"blank_{fill_index}")
        if user_input:
            correct_answer = answers[fill_index]
            if user_input.strip().lower() == correct_answer.lower():
                st.session_state.correct_words[fill_index] = correct_answer
                st.session_state.fill_index += 1
                st.session_state.feedback_message = "✅ Correct!"
                safe_rerun()
            else:
                st.session_state.feedback_message = "❌ Incorrect. Try again."
                safe_rerun()
    else:
        st.success("🎉 All blanks filled!")

    if st.session_state.feedback_message:
        st.info(st.session_state.feedback_message)
