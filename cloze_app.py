
import streamlit as st
import random
import re
import math

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

# Function
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

# Init
if "initialized" not in st.session_state:
    st.session_state.initialized = False

if start_button and paragraph_input:
    paragraphs = [p.strip() for p in paragraph_input.split("\n") if p.strip()]
    all_blocks = []
    for p in paragraphs:
        tokens, answers, positions = generate_cloze_data(p, missing_ratio)
        block = {
            "tokens": tokens,
            "answers": answers,
            "positions": positions,
            "correct_words": [None] * len(positions),
            "input_values": ["" for _ in positions],
            "feedback": ["" for _ in positions],
            "done": False
        }
        all_blocks.append(block)

    st.session_state.blocks = all_blocks
    st.session_state.current_idx = 0
    st.session_state.initialized = True

if st.session_state.initialized:
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

    # Paragraph rendering
    display_tokens = tokens[:]
    for i, pos in enumerate(positions):
        if correct_words[i] is not None:
            display_tokens[pos] = f"<u>{correct_words[i]}</u>"
    st.markdown("**Updated Paragraph:**", unsafe_allow_html=True)
    st.markdown("".join(display_tokens), unsafe_allow_html=True)

    # Input section
    st.markdown("""---
### 📝 Fill in the blanks:""")
    rows = math.ceil(len(positions) / 4)
    for r in range(rows):
        cols = st.columns(4)
        for c in range(4):
            i = r * 4 + c
            if i >= len(positions):
                break
            with cols[c]:
                label = f"#{i+1}"
                if correct_words[i] is not None:
                    st.text_input(label, value=correct_words[i], key=f"filled_{idx}_{i}", disabled=True, label_visibility='collapsed')
                else:
                    input_val = st.text_input(label, key=f"input_{idx}_{i}", label_visibility='collapsed')
                    if input_val:
                        block["input_values"][i] = input_val
                        if input_val.strip().lower() == answers[i].lower():
                            block["correct_words"][i] = answers[i]
                            block["feedback"][i] = "✅ Correct!"
                            safe_rerun()
                        else:
                            block["feedback"][i] = "❌ Try again"
                    if feedback[i]:
                        st.caption(feedback[i])

    if all(w is not None for w in correct_words) and not block["done"]:
        block["done"] = True
        st.balloons()

    if block["done"]:
        if idx + 1 < len(st.session_state.blocks):
            if st.button("➡ Next Paragraph"):
                st.session_state.current_idx += 1
                safe_rerun()
        else:
            st.success("🎉 All paragraphs completed!")
            total_words = sum(len(b["positions"]) for b in st.session_state.blocks)
            total_correct = sum(sum(w is not None for w in b["correct_words"]) for b in st.session_state.blocks)
            st.markdown(f"📊 **Final Report**")
            st.write(f"Total missing words: {total_words}")
            st.write(f"Correctly filled: {total_correct}")
            st.write(f"Accuracy: {total_correct/total_words:.1%}")
            if st.button("🔁 Start Over"):
                st.session_state.clear()
                safe_rerun()
