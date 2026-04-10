import os
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT_FILE = "system_prompt.txt"
FALLBACK_PHRASE    = "Уточните у администратора"

INPUT_PRICE_PER_M  = 0.150
OUTPUT_PRICE_PER_M = 0.600

def load_system_prompt() -> str:
    try:
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)

def get_answer(api_key: str, question: str, faq_content: str,
               system_prompt_template: str) -> dict:
    start = time.time()
    try:
        client = OpenAI(api_key=api_key)
        system_instruction = system_prompt_template.replace("{faq_content}", faq_content)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": question}
            ],
            temperature=0.0,
        )
        latency_ms = int((time.time() - start) * 1000)
        
        if response.choices and response.choices[0].message.content:
            answer = response.choices[0].message.content.strip()
        else:
            answer = FALLBACK_PHRASE
            
        try:
            in_tok  = response.usage.prompt_tokens
            out_tok = response.usage.completion_tokens
        except Exception:
            in_tok  = estimate_tokens(system_instruction + question)
            out_tok = estimate_tokens(answer)
            
        return {
            "answer":        answer,
            "input_tokens":  in_tok,
            "output_tokens": out_tok,
            "latency_ms":    latency_ms,
            "is_fallback":   answer.strip() == FALLBACK_PHRASE,
            "error":         None,
        }
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "answer":        f"⚠️ Техническая ошибка: {e}",
            "input_tokens":  0,
            "output_tokens": 0,
            "latency_ms":    latency_ms,
            "is_fallback":   False,
            "error":         str(e),
        }

def usd_cost(in_tok: int, out_tok: int) -> float:
    return (in_tok * INPUT_PRICE_PER_M + out_tok * OUTPUT_PRICE_PER_M) / 1_000_000

def init_state():
    defaults = {
        "chat_history":   [],
        "total_in_tok":   0,
        "total_out_tok":  0,
        "total_calls":    0,
        "fallback_count": 0,
        "error_count":    0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def main():
    st.set_page_config(page_title="SME FAQ Assistant", page_icon="🏥", layout="wide")
    init_state()

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .brand-header {
        background: linear-gradient(135deg, #0f2027, #1a3a4a, #0a5c66);
        border-radius: 12px; padding: 28px 32px 20px; margin-bottom: 24px;
        border-left: 5px solid #00d4aa;
    }
    .brand-header h1 { color: #ffffff; font-size: 1.9rem; margin:0; font-weight:600; }
    .brand-header p  { color: #8ecfc9; margin:4px 0 0; font-size:.92rem; }
    .chat-bubble-user {
        background: #e8f5f3; border-radius: 14px 14px 4px 14px;
        padding: 12px 16px; margin: 6px 0; max-width: 80%;
        margin-left: auto; color: #0d2b2b; font-size: .93rem;
    }
    .chat-bubble-bot {
        background: #f4fffe; border: 1px solid #c0e8e3;
        border-radius: 14px 14px 14px 4px; padding: 12px 16px;
        margin: 6px 0; max-width: 80%; color: #0d2b2b; font-size: .93rem;
    }
    .chat-bubble-fallback {
        background: #fff8e1; border: 1px solid #ffe082;
        border-radius: 14px 14px 14px 4px; padding: 12px 16px;
        margin: 6px 0; max-width: 80%; color: #5d4037; font-size: .93rem;
    }
    .chat-meta { font-family:'IBM Plex Mono',monospace; font-size:.72rem; color:#90a4ae; margin-top:4px; }
    .metric-card {
        background: #0f2027; border: 1px solid #1e4d5a; border-radius: 10px;
        padding: 14px 18px; margin-bottom: 10px; color: #fff;
    }
    .metric-card .label { font-size:.75rem; color:#8ecfc9; text-transform:uppercase; letter-spacing:.08em; }
    .metric-card .value { font-size:1.35rem; font-weight:600; font-family:'IBM Plex Mono',monospace; }
    .status-ok { color:#00d4aa; } .status-warn { color:#ffd54f; } .status-err { color:#ff6b6b; }
    div[data-testid="stButton"] button {
        background:#00d4aa; color:#0f2027; font-weight:600;
        border:none; border-radius:8px; padding:0.45rem 1.4rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="brand-header">
        <h1>🏥 SME FAQ Assistant</h1>
        <p>AI-powered customer support · GPT-4o-mini · Built for SME B2B deployment</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        env_api_key    = os.getenv("OPENAI_API_KEY", "")
        manual_api_key = st.text_input("OpenAI API Key", type="password", placeholder="Paste key if not in .env")
        api_key = env_api_key or manual_api_key
        if env_api_key:
            st.success("✅ API key loaded from .env")
        elif manual_api_key:
            st.success("✅ API key entered manually")
        else:
            st.warning("⚠️ No API key detected")

        st.divider()
        st.markdown("### 📂 FAQ Document")
        uploaded_file = st.file_uploader("Upload FAQ (.txt)", type=["txt"])

        st.divider()
        st.markdown("### 📊 FinOps Dashboard")
        s = st.session_state
        total_cost = usd_cost(s["total_in_tok"], s["total_out_tok"])
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="label">Queries</div><div class="value">{s["total_calls"]}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="label">Est. Cost</div><div class="value">${total_cost:.5f}</div></div>', unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            fb_pct = (s["fallback_count"] / max(1, s["total_calls"])) * 100
            fb_cls = "status-ok" if fb_pct < 20 else "status-warn"
            st.markdown(f'<div class="metric-card"><div class="label">Fallbacks</div><div class="value {fb_cls}">{s["fallback_count"]}</div></div>', unsafe_allow_html=True)
        with col4:
            err_cls = "status-ok" if s["error_count"] == 0 else "status-err"
            st.markdown(f'<div class="metric-card"><div class="label">Errors</div><div class="value {err_cls}">{s["error_count"]}</div></div>', unsafe_allow_html=True)
        tokens_used = s["total_in_tok"] + s["total_out_tok"]
        st.markdown(f'<div class="metric-card"><div class="label">Total Tokens</div><div class="value">{tokens_used:,}</div></div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat"):
            st.session_state["chat_history"] = []
            st.rerun()
        st.divider()
        st.markdown("<small style='color:#546e7a;'><b>D2C Monitoring Active</b><br>• Token cost tracked per query<br>• Fallback rate (&lt;20% = healthy)<br>• Errors logged in real time</small>", unsafe_allow_html=True)

    if not api_key:
        st.error("🔑 Please provide an OpenAI API key in `.env` or the sidebar.")
        st.stop()

    faq_content = ""
    if uploaded_file:
        try:
            faq_content = uploaded_file.read().decode("utf-8").strip()
            if not faq_content:
                st.error("Uploaded FAQ file is empty.")
                st.stop()
            with st.expander("📄 Preview FAQ document", expanded=False):
                st.text(faq_content[:2000] + ("…" if len(faq_content) > 2000 else ""))
        except Exception:
            st.error("Could not read the file. Upload a valid UTF-8 .txt file.")
            st.stop()
    else:
        st.info("⬅️ Upload your FAQ `.txt` file in the sidebar to begin.")
        st.stop()

    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            meta = msg.get("meta", {})
            bubble_cls = "chat-bubble-fallback" if meta.get("is_fallback") else "chat-bubble-bot"
            icon = "⚠️" if meta.get("is_fallback") else "🤖"
            tok_info = (f"in:{meta.get('input_tokens',0)} · out:{meta.get('output_tokens',0)} · "
                        f"${usd_cost(meta.get('input_tokens',0), meta.get('output_tokens',0)):.5f} · "
                        f"{meta.get('latency_ms',0)} ms") if meta else ""
            st.markdown(f'<div class="{bubble_cls}">{icon} {msg["content"]}<div class="chat-meta">{tok_info}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    col_q, col_btn = st.columns([5, 1])
    with col_q:
        user_question = st.text_input("Вопрос:", placeholder="Например: Как записаться на прием?", label_visibility="collapsed")
    with col_btn:
        send = st.button("Send →")

    if send:
        if not user_question.strip():
            st.warning("Введите вопрос.")
            st.stop()
        system_prompt_template = load_system_prompt()
        if not system_prompt_template:
            st.error("`system_prompt.txt` not found.")
            st.stop()
        st.session_state["chat_history"].append({"role": "user", "content": user_question})
        with st.spinner("Thinking…"):
            result = get_answer(api_key, user_question, faq_content, system_prompt_template)
        st.session_state["total_calls"]    += 1
        st.session_state["total_in_tok"]   += result["input_tokens"]
        st.session_state["total_out_tok"]  += result["output_tokens"]
        if result["is_fallback"]:  st.session_state["fallback_count"] += 1
        if result["error"]:        st.session_state["error_count"]    += 1
        st.session_state["chat_history"].append({"role": "assistant", "content": result["answer"], "meta": result})
        st.rerun()

if __name__ == "__main__":
    main()