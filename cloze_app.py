
import streamlit as st
import random
import re
import math
from gtts import gTTS
import base64
from io import BytesIO

def tts_base64(text):
    tts = gTTS(text)
    buf = BytesIO()
    tts.write_to_fp(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:audio/mp3;base64,{b64}"

# Updated suffix list
smart_suffixes = [
    "ing", "ed", "ly", "ous", "ful", "less", "ness", "ment", "ion", "tion",
    "ity", "al", "ive", "able", "ible", "ship", "ence", "ance", "est", "ish"
]

def is_candidate(word):
    word = word.lower().strip(".,!?;")
    return len(word) > 3 and any(word.endswith(suffix) for suffix in smart_suffixes)

def select_keywords(words, ratio=0.2):
    word_indices = [i for i, w in enumerate(words) if re.match(r"\w+$", w) and is_candidate(w)]
    target_count = max(1, int(len([w for w in words if re.match(r"\w+$", w)]) * ratio))

    if len(word_indices) < target_count:
        all_indices = [i for i, w in enumerate(words) if re.match(r"\w+$", w) and len(w) > 3 and i not in word_indices]
        needed = target_count - len(word_indices)
        if len(all_indices) > needed:
            word_indices += random.sample(all_indices, needed)
        else:
            word_indices += all_indices  # add all if not enough

    return sorted(word_indices[:target_count])

def generate_cloze_paragraphs(paragraphs, ratio):
    blocks = []
    for p in paragraphs:
        words = re.findall(r"\w+|\W", p)
        selected_indices = select_keywords(words, ratio)
        answers = [words[i] for i in selected_indices]
        cloze_words = words[:]
        for i in selected_indices:
            cloze_words[i] = "____"
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

st.set_page_config(page_title="Cloze App v7.2", layout="wide")
st.title("🧠 Cloze Listening App (v7.2 Smart + Fallback)")

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
            display_tokens[pos] = f"<u>{correct_words[i]}</u>"
        else:
            display_tokens[pos] = f"<b>[{i+1}] ____</b>"
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
