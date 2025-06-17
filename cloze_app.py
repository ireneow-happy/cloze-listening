
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

# Sidebar settings
st.sidebar.header("Step 1: Input Settings")
paragraph_input = st.sidebar.text_area("Enter paragraphs (one per line):", height=200)
missing_ratio = st.sidebar.slider("Select missing word ratio:", 0.05, 0.9, 0.3, step=0.05)
start_button = st.sidebar.button("✅ Generate Cloze Paragraphs")

# Initial state
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

if start_button and paragraph_input:
    paragraphs = [p.strip() for p in paragraph_input.split("\n") if p.strip()]
    tokens, answers, positions = generate_cloze_data(paragraphs[0], missing_ratio)
    st.session_state.tokens = tokens
    st.session_state.answers = answers
    st.session_state.positions = positions
    st.session_state.correct_words = [None] * len(positions)
    st.session_state.total_missing = len(positions)
    st.session_state.feedback = ["" for _ in range(len(positions))]
    st.session_state.input_values = ["" for _ in range(len(positions))]
    st.session_state.initialized = True
    st.session_state.done = False

if st.session_state.initialized:
    tokens = st.session_state.tokens
    answers = st.session_state.answers
    positions = st.session_state.positions
    correct_words = st.session_state.correct_words
    input_values = st.session_state.input_values
    feedback = st.session_state.feedback
    total = st.session_state.total_missing

    st.subheader(f"Paragraph 1 of 1")
    st.markdown(f"🟢 **Progress: {sum(w is not None for w in correct_words)} / {total}**")

    # Show updated paragraph
    display_tokens = tokens[:]
    for i, pos in enumerate(positions):
        if correct_words[i] is not None:
            display_tokens[pos] = f"<u>{correct_words[i]}</u>"
    st.markdown("**Updated Paragraph:**", unsafe_allow_html=True)
    st.markdown("".join(display_tokens), unsafe_allow_html=True)

    # Multi-column layout for compact inputs
    cols = st.columns(len(positions))
    all_correct = True

    for i, pos in enumerate(positions):
        with cols[i]:
            label = f"#{i+1}"
            if correct_words[i] is not None:
                st.text_input(label, value=correct_words[i], key=f"filled_{i}", disabled=True, label_visibility='collapsed')
            else:
                input_val = st.text_input(label, key=f"input_{i}", label_visibility='collapsed')
                if input_val:
                    st.session_state.input_values[i] = input_val
                    if input_val.strip().lower() == answers[i].lower():
                        st.session_state.correct_words[i] = answers[i]
                        st.session_state.feedback[i] = "✅ Correct!"
                        safe_rerun()
                    else:
                        st.session_state.feedback[i] = "❌ Try again"
                        all_correct = False
                else:
                    all_correct = False
                if feedback[i]:
                    st.caption(feedback[i])

    if all_correct and not st.session_state.done:
        st.session_state.done = True
        st.balloons()

    if st.session_state.done:
        if st.button("🔁 Start Over"):
            st.session_state.clear()
            safe_rerun()
