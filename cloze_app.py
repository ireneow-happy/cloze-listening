
import streamlit as st
import random
import re
import math
import spacy
from gtts import gTTS
import base64
from io import BytesIO

# Load spaCy model once
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

def tts_base64(text):
    tts = gTTS(text)
    buf = BytesIO()
    tts.write_to_fp(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:audio/mp3;base64,{b64}"

def get_important_indices(doc):
    indices = []
    for token in doc:
        if token.dep_ in {"ROOT", "nsubj", "dobj", "attr", "acomp"} and token.pos_ in {"VERB", "NOUN", "ADJ"}:
            indices.append(token.i)
    return indices

def generate_cloze_paragraphs(paragraphs, ratio):
    blocks = []
    for p in paragraphs:
        doc = nlp(p)
        words = [token.text_with_ws for token in doc]
        candidate_indices = get_important_indices(doc)
        if not candidate_indices:
            candidate_indices = [i for i, token in enumerate(doc) if token.pos_ in {"NOUN", "VERB", "ADJ"}]
        num_to_remove = max(1, int(len(candidate_indices) * ratio))
        selected_indices = sorted(random.sample(candidate_indices, min(num_to_remove, len(candidate_indices))))
        answers = [words[i].strip() for i in selected_indices]
        cloze_words = words[:]
        for i in selected_indices:
            cloze_words[i] = "____ "
        blocks.append({
            "original": p,
            "tokens": cloze_words,
            "answers": answers,
            "positions": selected_indices,
            "correct_words": [None] * len(selected_indices),
            "input_values": ["" for _ in selected_indices],
            "feedback": ["" for _ in selected_indices],
            "done": False
        })
    return blocks

st.set_page_config(page_title="Cloze App v7", layout="wide")
st.title("🧠 Cloze Listening Practice (Smart POS & Core Word Selection)")

if "initialized" not in st.session_state:
    st.session_state.initialized = False

if not st.session_state.initialized:
    st.sidebar.header("Step 1: Input")
    paragraph_input = st.sidebar.text_area("Enter paragraphs (1+):", height=200)
    missing_ratio = st.sidebar.slider("Missing Word Ratio", 0.05, 0.9, 0.3, step=0.05)
    generate = st.sidebar.button("✅ Generate Cloze Paragraphs")

    if generate:
        paragraphs = [p.strip() for p in paragraph_input.split("\n") if p.strip()]
        if paragraphs:
            st.session_state.blocks = generate_cloze_paragraphs(paragraphs, missing_ratio)
            st.session_state.current_idx = 0
            st.session_state.initialized = True
            st.rerun()

if st.session_state.get("initialized", False):
    idx = st.session_state.current_idx
    block = st.session_state.blocks[idx]
    tokens = block["tokens"]
    answers = block["answers"]
    positions = block["positions"]
    correct_words = block["correct_words"]
    input_values = block["input_values"]
    feedback = block["feedback"]
    total = len(positions)

    st.subheader(f"Paragraph {idx+1} of {len(st.session_state.blocks)}")
    st.markdown(f"🟢 Progress: {sum(w is not None for w in correct_words)} / {total}")
    st.audio(tts_base64(block["original"]), format="audio/mp3")

    display_tokens = tokens[:]
    for i, pos in enumerate(positions):
        if correct_words[i] is not None:
            display_tokens[pos] = f"<u>{correct_words[i]}</u> "
        else:
            display_tokens[pos] = f"<b>[{i+1}] ____</b> "
    st.markdown("**Cloze Paragraph:**", unsafe_allow_html=True)
    st.markdown("".join(display_tokens), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📝 Fill in the blanks:")

    rows = math.ceil(len(positions) / 4)
    for r in range(rows):
        cols = st.columns(4)
        for c in range(4):
            i = r * 4 + c
            if i >= len(positions):
                break
            with cols[c]:
                label = f"[{i+1}]"
                key = f"input_{idx}_{i}"
                if correct_words[i] is not None:
                    st.text_input(label, value=correct_words[i], key=f"filled_{idx}_{i}", disabled=True)
                else:
                    val = st.text_input(label, value=input_values[i], key=key)
                    if val and val.strip().lower() == answers[i].lower():
                        correct_words[i] = answers[i]
                        feedback[i] = "✅ Correct!"
                        st.rerun()
                    elif val:
                        input_values[i] = val
                        feedback[i] = "❌ Try again"
                    if feedback[i]:
                        st.caption(feedback[i])

    if all(w is not None for w in correct_words) and not block["done"]:
        block["done"] = True
        st.balloons()

    if block["done"]:
        with st.expander("📄 Original Paragraph"):
            st.markdown(block["original"])

        if idx + 1 < len(st.session_state.blocks):
            if st.button("➡ Proceed to Next Paragraph"):
                st.session_state.current_idx += 1
                st.rerun()
        else:
            st.success("🎉 All paragraphs completed!")
            if st.button("🔁 Start Over"):
                st.session_state.clear()
                st.rerun()
