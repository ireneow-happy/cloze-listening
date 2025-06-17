# Cloze Listening App v7 (with POS + Core Meaning Selection)

## Features
- 🎯 Smart missing word selection based on sentence structure
- ✅ Uses POS tagging and dependency parsing
- 🔊 TTS for paragraph playback
- 🧠 More meaningful cloze practice

## Run
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run cloze_app.py
```