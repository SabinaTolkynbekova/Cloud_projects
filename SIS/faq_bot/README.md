# FAQ AI Assistant

## How to run

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create .env file:
```env
GEMINI_API_KEY=your_key_here
```

3. Run:
```bash
python -m streamlit run app.py
```

## Setup Notes
- The system uses strict FAQ-based answering using the Google Gemini API (`gemini-1.5-flash`).
- Requires absolutely strict constraints: NO outside knowledge, NO inference.
- If the exact answer is not found in the uploaded text, the bot will strictly return:
  "Уточните у администратора"