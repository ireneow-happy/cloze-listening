
import streamlit as st
import random
import re
import math
from gtts import gTTS
import base64
from io import BytesIO

def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            st.warning("Please update your Streamlit version.")

def tts_base64(text):
    tts = gTTS(text)
    buf = BytesIO()
    tts.write_to_fp(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:audio/mp3;base64,{b64}"

st.set_page_config(page_title="Cloze Listening with TTS", layout="wide")
st.title("🎧 English Cloze Listening App with TTS")

if "initialized" not in st.session_state:
    st.session_state.initialized = False

# Sidebar input
if not st.session_state.initialized:
    st.sidebar.header("Step 1: Input Settings")
    paragraph_input = st.sidebar.text_area("Enter any number of paragraphs (one per line):", height=200, key="input_area")
    missing_ratio = st.sidebar.slider("Select missing word ratio:", 0.05, 0.9, 0.3, step=0.05)
    start_button = st.sidebar.button("✅ Generate Cloze Paragraphs")

    if start_button:
        paragraphs = [p.strip() for p in paragraph_input.split("\n") if p.strip()]
        if len(paragraphs) >= 1:
            all_blocks = []
            for p in paragraphs:
                words = re.findall(r"\b\w+\b|\W", p)
                word_indices = [i for i, w in enumerate(words) if re.match(r"\w+", w)]
                num_to_remove = max(1, int(len(word_indices) * missing_ratio))
                missing_indices = sorted(random.sample(word_indices, num_to_remove))
                answers = [words[i] for i in missing_indices]
                cloze_words = words[:]
                for i in missing_indices:
                    cloze_words[i] = "____"
                all_blocks.append({
                    "original": p,
                    "tokens": cloze_words,
                    "answers": answers,
                    "positions": missing_indices,
                    "correct_words": [None] * len(missing_indices),
                    "input_values": ["" for _ in missing_indices],
                    "feedback": ["" for _ in missing_indices],
                    "done": False
                })

            st.session_state.blocks = all_blocks
            st.session_state.current_idx = 0
            st.session_state.initialized = True
            st.session_state.ratio = missing_ratio
            safe_rerun()

# Main logic
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
    st.markdown(f"🟢 **Progress: {sum(w is not None for w in correct_words)} / {total}**")

    # Always display audio bar
    b64_audio = tts_base64(block["original"])
    st.audio(b64_audio, format="audio/mp3")

    # Cloze paragraph with numbering
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
                key_name = f"input_{idx}_{i}"
                if correct_words[i] is not None:
                    st.text_input(label, value=correct_words[i], key=f"filled_{idx}_{i}", disabled=True, label_visibility='visible')
                else:
                    input_val = st.text_input(label, value=block["input_values"][i], key=key_name, label_visibility='visible')
                    if input_val and input_val.strip().lower() == answers[i].lower():
                        block["correct_words"][i] = answers[i]
                        block["feedback"][i] = "✅ Correct!"
                        safe_rerun()
                    elif input_val:
                        block["input_values"][i] = input_val
                        block["feedback"][i] = "❌ Try again"
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
                safe_rerun()
        else:
            st.success("🎉 All paragraphs completed!")
            if st.button("🔁 Start Over"):
                st.session_state.clear()
                safe_rerun()
