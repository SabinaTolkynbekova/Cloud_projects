# SME FAQ Assistant

AI-powered customer support chatbot for SME B2B deployment. Built with OpenAI GPT-4o-mini + Streamlit.

## Features
- **Auto-loads** `faq.txt` from the project directory — no upload needed by default
- **Custom FAQ upload** — switch to upload mode in the sidebar for a different FAQ file
- **Conversation memory** — keeps context across multiple turns (last 6 exchanges)
- **FinOps Dashboard** — real-time token cost, fallback rate, avg latency, error tracking
- **Strict FAQ-only answers** — returns "Уточните у администратора" if the answer is not in the FAQ

## Project Structure
```
.
├── app.py               # Main Streamlit application
├── faq.txt              # Default FAQ document (auto-loaded)
├── system_prompt.txt    # LLM system prompt template
├── requirements.txt     # Python dependencies
├── .env                 # API key (not committed to git)
└── README.md
```

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create `.env` file
```env
OPENAI_API_KEY=sk-...your-key-here...
```

### 3. Run
```bash
python -m streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Usage
- The bundled `faq.txt` loads automatically — just type your question and click **Send →**
- To use a different FAQ, select **"⬆️ Upload custom FAQ"** in the sidebar
- The **FinOps Dashboard** in the sidebar shows cost, tokens, fallback rate, and latency in real time

## D2C Monitoring (Detect to Correct)
| Metric | Healthy threshold |
|---|---|
| Fallback rate | < 20% |
| Error count | 0 |
| Avg latency | < 3000 ms |
| Token cost | Tracked per query |

## IT4IT Value Streams
| Stream | Description |
|---|---|
| **S2P** | Automates FAQ-based customer support for dental/medical SMEs in Almaty |
| **R2D** | Architected via AI agent (see session logs); system prompt enforces strict FAQ-only answers |
| **R2F** | Streamlit web interface — accessible via browser, no installation required for end users |
| **D2C** | Real-time FinOps dashboard: token cost, fallback rate, error count, latency tracking |