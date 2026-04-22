import os
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT_FILE = "system_prompt.txt"
FAQ_FILE = "faq.txt"
FALLBACK_PHRASE = "Уточните у администратора"
MODEL = "gpt-4o-mini"
INPUT_PRICE_PER_M = 0.150
OUTPUT_PRICE_PER_M = 0.600
MAX_HISTORY_TURNS = 6

SUGGESTED_QUESTIONS = [
    "Как записаться на прием?",
    "Принимаете ли вы страховку?",
    "Сколько стоит консультация?",
    "Где находится клиника?",
    "Работаете ли вы в выходные?",
    "Что делать при острой боли?",
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_text_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def usd_cost(in_tok: int, out_tok: int) -> float:
    return (in_tok * INPUT_PRICE_PER_M + out_tok * OUTPUT_PRICE_PER_M) / 1_000_000


# ── LLM call ──────────────────────────────────────────────────────────────────
def get_answer(
    api_key: str, question: str, faq_content: str, system_template: str, history: list
) -> dict:
    start = time.time()
    try:
        client = OpenAI(api_key=api_key)
        system_msg = system_template.replace("{faq_content}", faq_content)
        trimmed = history[-(MAX_HISTORY_TURNS * 2) :]
        messages = (
            [{"role": "system", "content": system_msg}]
            + trimmed
            + [{"role": "user", "content": question}]
        )
        response = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.0
        )
        latency_ms = int((time.time() - start) * 1000)
        answer = (
            response.choices[0].message.content.strip()
            if response.choices and response.choices[0].message.content
            else FALLBACK_PHRASE
        )
        try:
            in_tok = response.usage.prompt_tokens
            out_tok = response.usage.completion_tokens
        except Exception:
            in_tok = max(1, len(system_msg + question) // 4)
            out_tok = max(1, len(answer) // 4)
        return {
            "answer": answer,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "latency_ms": latency_ms,
            "is_fallback": answer.strip() == FALLBACK_PHRASE,
            "error": None,
        }
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "answer": f"⚠️ Техническая ошибка: {e}",
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": latency_ms,
            "is_fallback": False,
            "error": str(e),
        }


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "chat_history": [],
        "llm_history": [],
        "total_in_tok": 0,
        "total_out_tok": 0,
        "total_calls": 0,
        "fallback_count": 0,
        "error_count": 0,
        "latencies": [],
        "questions_log": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def record_result(result: dict, question: str):
    s = st.session_state
    s["total_calls"] += 1
    s["total_in_tok"] += result["input_tokens"]
    s["total_out_tok"] += result["output_tokens"]
    s["latencies"].append(result["latency_ms"])
    s["questions_log"].append(
        {
            "question": question,
            "is_fallback": result["is_fallback"],
            "cost": usd_cost(result["input_tokens"], result["output_tokens"]),
            "latency_ms": result["latency_ms"],
        }
    )
    if result["is_fallback"]:
        s["fallback_count"] += 1
    if result["error"]:
        s["error_count"] += 1
    s["llm_history"].append({"role": "user", "content": question})
    s["llm_history"].append({"role": "assistant", "content": result["answer"]})
    s["chat_history"].append(
        {"role": "assistant", "content": result["answer"], "meta": result}
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="SME FAQ Assistant", page_icon="🏥", layout="wide")
    init_state()

    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    /* ── Global dark theme ── */
    html, body, [class*="css"],
    .main, .main .block-container,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"] {
        font-family: 'DM Sans', sans-serif !important;
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #111827 !important;
        border-right: 1px solid #1f2937 !important;
    }
    [data-testid="stSidebar"] * { color: #e5e7eb !important; }
    [data-testid="stSidebar"] .stTextInput input {
        background: #1f2937 !important;
        border: 1px solid #374151 !important;
        color: #f9fafb !important;
        border-radius: 8px !important;
    }

    /* ── Hide streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Page header ── */
    .page-header {
        display: flex; align-items: center; gap: 16px;
        padding: 22px 28px;
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        border-radius: 14px; margin-bottom: 20px;
    }
    .page-header h1 { margin:0; font-size:1.45rem; font-weight:700; color:#fff; }
    .page-header p  { margin:3px 0 0; font-size:.82rem; color:rgba(255,255,255,.75); }

    /* ── Tabs ── */
    [data-testid="stTabs"] [role="tablist"] {
        background: #161b22 !important;
        border-radius: 12px !important;
        padding: 5px !important; gap: 4px !important;
        border-bottom: none !important;
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: .88rem !important;
        color: #8b949e !important;
        border: none !important;
        padding: 8px 20px !important;
        background: transparent !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #0ea5e9 !important;
        color: #fff !important;
        box-shadow: 0 2px 10px rgba(14,165,233,.4) !important;
    }
    [data-testid="stTabs"] [role="tabpanel"] {
        background: transparent !important;
        padding: 0 !important;
    }

    /* ── Chat messages ── */
    .bubble-row-user { display:flex; justify-content:flex-end; margin:10px 0; }
    .bubble-row-bot  { display:flex; justify-content:flex-start; margin:10px 0; }
    .bubble-user {
        background: linear-gradient(135deg, #0ea5e9, #0284c7);
        color: #fff; border-radius: 18px 18px 4px 18px;
        padding: 12px 18px; max-width: 70%;
        font-size: .92rem; line-height: 1.55;
        box-shadow: 0 4px 14px rgba(14,165,233,.25);
    }
    .bubble-bot {
        background: #1c2333; border: 1px solid #30363d;
        color: #e6edf3; border-radius: 18px 18px 18px 4px;
        padding: 12px 18px; max-width: 70%;
        font-size: .92rem; line-height: 1.55;
    }
    .bubble-fallback {
        background: #2d1f00; border: 1px solid #6e4c00;
        color: #fbbf24; border-radius: 18px 18px 18px 4px;
        padding: 12px 18px; max-width: 70%;
        font-size: .92rem; line-height: 1.55;
    }
    .bubble-meta {
        font-family: 'DM Mono', monospace;
        font-size: .68rem; color: #484f58; margin-top: 6px;
    }

    /* ── Empty chat state ── */
    .chat-empty {
        text-align: center; padding: 48px 0 32px;
        color: #484f58; font-size: .95rem;
    }
    .chat-empty .icon { font-size: 2.8rem; margin-bottom: 10px; }
    .chat-empty .label { color: #8b949e; }

    /* ── Text input — force dark ── */
    [data-testid="stTextInput"] > div > div {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
    }
    [data-testid="stTextInput"] input {
        background: #161b22 !important;
        color: #e6edf3 !important;
        border: none !important;
        font-size: .95rem !important;
        caret-color: #0ea5e9 !important;
    }
    [data-testid="stTextInput"] input::placeholder { color: #484f58 !important; }
    [data-testid="stTextInput"] input:focus { box-shadow: none !important; }

    /* ── Buttons ── */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
        color: #fff !important; border: none !important;
        border-radius: 10px !important; font-weight: 600 !important;
        padding: 0.5rem 1.4rem !important; font-size: .9rem !important;
        box-shadow: 0 2px 10px rgba(14,165,233,.3) !important;
        transition: transform .15s !important;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(14,165,233,.45) !important;
    }

    /* ── Sidebar stat cards ── */
    .stat-card {
        background: #1f2937; border: 1px solid #374151;
        border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
    }
    .stat-card .lbl {
        font-size: .7rem; color: #6b7280 !important;
        text-transform: uppercase; letter-spacing: .07em;
    }
    .stat-card .val {
        font-size: 1.3rem; font-weight: 600;
        font-family: 'DM Mono', monospace; color: #f9fafb !important;
    }
    .c-ok   { color: #34d399 !important; }
    .c-warn { color: #fbbf24 !important; }
    .c-err  { color: #f87171 !important; }

    /* ── Architect Dashboard ── */
    .section-label {
        font-size: .72rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: .1em;
        color: #484f58; margin: 24px 0 12px;
        padding-bottom: 6px;
        border-bottom: 1px solid #21262d;
    }
    .kpi-card {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 14px; padding: 20px 22px;
        border-top: 3px solid #0ea5e9;
    }
    .kpi-card.ok-t   { border-top-color: #10b981; }
    .kpi-card.warn-t { border-top-color: #f59e0b; }
    .kpi-card.err-t  { border-top-color: #ef4444; }
    .kpi-card .kl { font-size:.72rem; color:#484f58; text-transform:uppercase; letter-spacing:.07em; margin-bottom:6px; }
    .kpi-card .kv { font-size:2rem; font-weight:700; font-family:'DM Mono',monospace; color:#e6edf3; }
    .kpi-card .ks { font-size:.75rem; color:#484f58; margin-top:4px; }

    .q-list-wrap {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 14px; padding: 18px 20px;
    }
    .q-list-title { font-size:.75rem; font-weight:600; color:#484f58; text-transform:uppercase; letter-spacing:.07em; margin-bottom:12px; }
    .q-row { display:flex; align-items:flex-start; gap:10px; padding:9px 0; border-bottom:1px solid #21262d; font-size:.88rem; color:#c9d1d9; }
    .q-row:last-child { border-bottom:none; }
    .dot-ok   { width:8px; height:8px; border-radius:50%; background:#10b981; margin-top:5px; flex-shrink:0; }
    .dot-fail { width:8px; height:8px; border-radius:50%; background:#ef4444; margin-top:5px; flex-shrink:0; }
    .q-sub    { font-size:.72rem; color:#484f58; margin-top:2px; }

    .gap-pill {
        background: #1a1200; border: 1px solid #6e4c00;
        border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
        font-size: .88rem; color: #fbbf24;
    }
    .gap-pill .rec { font-size:.75rem; color:#78350f; margin-top:4px; }
    .health-ok {
        background: #051a0e; border: 1px solid #16a34a;
        border-radius: 10px; padding: 14px 18px;
        font-size: .9rem; color: #34d399; font-weight: 500;
    }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        env_key = os.getenv("OPENAI_API_KEY", "")
        manual_key = st.text_input(
            "OpenAI API Key", type="password", placeholder="sk-..."
        )
        api_key = env_key or manual_key
        if env_key:
            st.success("✅ Loaded from .env")
        elif manual_key:
            st.success("✅ Entered manually")
        else:
            st.warning("⚠️ No API key")

        st.divider()
        st.markdown("### 📂 FAQ Source")
        faq_source = st.radio(
            "",
            ["📁 Bundled faq.txt", "⬆️ Upload custom FAQ"],
            index=0,
            label_visibility="collapsed",
        )
        uploaded_file = None
        if faq_source == "⬆️ Upload custom FAQ":
            uploaded_file = st.file_uploader("Upload .txt", type=["txt"])

        st.divider()
        st.markdown("### 📊 FinOps")
        s = st.session_state
        total_cost = usd_cost(s["total_in_tok"], s["total_out_tok"])
        avg_lat = (
            int(sum(s["latencies"]) / len(s["latencies"])) if s["latencies"] else 0
        )
        fb_pct = (s["fallback_count"] / max(1, s["total_calls"])) * 100

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div class="stat-card"><div class="lbl">Queries</div><div class="val">{s["total_calls"]}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="stat-card"><div class="lbl">Cost</div><div class="val">${total_cost:.4f}</div></div>',
                unsafe_allow_html=True,
            )
        c3, c4 = st.columns(2)
        with c3:
            fc = "c-warn" if fb_pct >= 20 else "c-ok"
            st.markdown(
                f'<div class="stat-card"><div class="lbl">Fallbacks</div><div class="val {fc}">{s["fallback_count"]}</div></div>',
                unsafe_allow_html=True,
            )
        with c4:
            ec = "c-err" if s["error_count"] > 0 else "c-ok"
            st.markdown(
                f'<div class="stat-card"><div class="lbl">Errors</div><div class="val {ec}">{s["error_count"]}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="stat-card"><div class="lbl">Avg Latency</div><div class="val">{avg_lat} ms</div></div>',
            unsafe_allow_html=True,
        )

        if st.button("🗑️ Clear session"):
            for k in ["chat_history", "llm_history", "latencies", "questions_log"]:
                st.session_state[k] = []
            for k in [
                "total_in_tok",
                "total_out_tok",
                "total_calls",
                "fallback_count",
                "error_count",
            ]:
                st.session_state[k] = 0
            st.rerun()

        st.divider()
        st.markdown(
            "<small style='color:#374151'>D2C Monitoring Active<br>Fallback &lt;20% · Errors = 0 · Latency &lt;3s</small>",
            unsafe_allow_html=True,
        )

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(
        """
    <div class="page-header">
        <div style="font-size:2rem">🏥</div>
        <div>
            <h1>SME FAQ Assistant</h1>
            <p>AI-powered customer support for dental clinics · Powered by GPT-4o-mini</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── Gate ──────────────────────────────────────────────────────────────────
    if not api_key:
        st.error("🔑 Укажите OpenAI API key в .env файле или в боковой панели.")
        st.stop()

    # ── Resolve FAQ ───────────────────────────────────────────────────────────
    if faq_source == "📁 Bundled faq.txt":
        faq_content = load_text_file(FAQ_FILE)
        if not faq_content:
            st.error(f"`{FAQ_FILE}` не найден. Положите его рядом с `app.py`.")
            st.stop()
    else:
        if not uploaded_file:
            st.info("⬅️ Загрузите FAQ файл в боковой панели.")
            st.stop()
        try:
            faq_content = uploaded_file.read().decode("utf-8").strip()
        except Exception:
            st.error("Не удалось прочитать файл.")
            st.stop()
        if not faq_content:
            st.error("Файл пустой.")
            st.stop()

    system_template = load_text_file(SYSTEM_PROMPT_FILE)
    if not system_template:
        st.error(f"`{SYSTEM_PROMPT_FILE}` не найден.")
        st.stop()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_chat, tab_arch = st.tabs(["💬  Customer Chat", "🏗️  Architect Dashboard"])

    # ══════════════════════════════════════════════════════════════════════════
    # CUSTOMER CHAT
    # ══════════════════════════════════════════════════════════════════════════
    with tab_chat:
        if not st.session_state["chat_history"]:
            st.markdown(
                """
            <div class="chat-empty">
                <div class="icon">💬</div>
                <div class="label">Задайте вопрос о клинике или выберите один из частых:</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            cols = st.columns(3)
            for i, q in enumerate(SUGGESTED_QUESTIONS):
                if cols[i % 3].button(q, key=f"sug_{i}"):
                    st.session_state["chat_history"].append(
                        {"role": "user", "content": q}
                    )
                    with st.spinner(""):
                        result = get_answer(
                            api_key,
                            q,
                            faq_content,
                            system_template,
                            st.session_state["llm_history"],
                        )
                    record_result(result, q)
                    st.rerun()
        else:
            for msg in st.session_state["chat_history"]:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="bubble-row-user">'
                        f'<div class="bubble-user">{msg["content"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    meta = msg.get("meta", {})
                    cls = "bubble-fallback" if meta.get("is_fallback") else "bubble-bot"
                    icon = "⚠️ " if meta.get("is_fallback") else ""
                    meta_line = (
                        (
                            f'<div class="bubble-meta">'
                            f"{meta.get('latency_ms', 0)} ms · "
                            f"${usd_cost(meta.get('input_tokens', 0), meta.get('output_tokens', 0)):.5f}"
                            f"</div>"
                        )
                        if meta
                        else ""
                    )
                    st.markdown(
                        f'<div class="bubble-row-bot">'
                        f'<div class="{cls}">{icon}{msg["content"]}{meta_line}</div></div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        col_q, col_btn = st.columns([6, 1])
        with col_q:
            user_question = st.text_input(
                "",
                placeholder="Введите ваш вопрос…",
                label_visibility="collapsed",
                key="user_input",
            )
        with col_btn:
            send = st.button("Отправить →")

        if send:
            if not user_question.strip():
                st.warning("Введите вопрос.")
                st.stop()
            st.session_state["chat_history"].append(
                {"role": "user", "content": user_question}
            )
            with st.spinner(""):
                result = get_answer(
                    api_key,
                    user_question,
                    faq_content,
                    system_template,
                    st.session_state["llm_history"],
                )
            record_result(result, user_question)
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # ARCHITECT DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    with tab_arch:
        s = st.session_state

        if s["total_calls"] == 0:
            st.markdown(
                """
            <div class="chat-empty" style="padding:60px 0">
                <div class="icon">🏗️</div>
                <div style="font-size:1rem; font-weight:500; color:#8b949e">Architect Dashboard</div>
                <div class="label" style="margin-top:6px; font-size:.88rem">
                    Задайте вопросы в чате — здесь появятся бизнес-инсайты,<br>
                    анализ пробелов в FAQ и D2C мониторинг.
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            st.stop()

        fb_pct = (s["fallback_count"] / s["total_calls"]) * 100
        avg_lat = (
            int(sum(s["latencies"]) / len(s["latencies"])) if s["latencies"] else 0
        )
        coverage = 100 - fb_pct
        total_cost = usd_cost(s["total_in_tok"], s["total_out_tok"])

        # ── S2P ───────────────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label">📐 Strategy to Portfolio — Business Value</div>',
            unsafe_allow_html=True,
        )
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            t = "ok-t" if coverage >= 80 else "warn-t"
            vc = "#10b981" if coverage >= 80 else "#f59e0b"
            st.markdown(
                f'<div class="kpi-card {t}"><div class="kl">FAQ Coverage</div><div class="kv" style="color:{vc}">{coverage:.0f}%</div><div class="ks">Вопросов отвечено из FAQ</div></div>',
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f'<div class="kpi-card"><div class="kl">Queries Handled</div><div class="kv">{s["total_calls"]}</div><div class="ks">Обращений в сессии</div></div>',
                unsafe_allow_html=True,
            )
        with k3:
            t = "warn-t" if s["fallback_count"] > 0 else "ok-t"
            vc = "#f59e0b" if s["fallback_count"] > 0 else "#10b981"
            st.markdown(
                f'<div class="kpi-card {t}"><div class="kl">Escalated to Admin</div><div class="kv" style="color:{vc}">{s["fallback_count"]}</div><div class="ks">Не найдено в FAQ</div></div>',
                unsafe_allow_html=True,
            )
        with k4:
            st.markdown(
                f'<div class="kpi-card"><div class="kl">Session Cost</div><div class="kv">${total_cost:.4f}</div><div class="ks">USD · GPT-4o-mini</div></div>',
                unsafe_allow_html=True,
            )

        # ── R2F ───────────────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label">📋 Request to Fulfill — Customer Demand Map</div>',
            unsafe_allow_html=True,
        )
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown(
                '<div class="q-list-wrap"><div class="q-list-title">Все вопросы сессии</div>',
                unsafe_allow_html=True,
            )
            for entry in s["questions_log"]:
                dot = "dot-fail" if entry["is_fallback"] else "dot-ok"
                label = "не найдено в FAQ" if entry["is_fallback"] else "отвечено"
                st.markdown(
                    f'<div class="q-row"><div class="{dot}"></div>'
                    f"<div><div>{entry['question']}</div>"
                    f'<div class="q-sub">{label} · {entry["latency_ms"]} ms</div></div></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
        with col_right:
            if len(s["latencies"]) > 1:
                st.markdown(
                    '<div class="q-list-wrap"><div class="q-list-title">Latency по запросам (ms)</div>',
                    unsafe_allow_html=True,
                )
                st.line_chart({"Latency (ms)": s["latencies"]}, height=200)
                st.markdown("</div>", unsafe_allow_html=True)

        # ── D2C ───────────────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label">🩺 Detect to Correct — System Health</div>',
            unsafe_allow_html=True,
        )
        d1, d2, d3 = st.columns(3)
        with d1:
            t = "warn-t" if avg_lat >= 3000 else "ok-t"
            vc = "#f59e0b" if avg_lat >= 3000 else "#10b981"
            st.markdown(
                f'<div class="kpi-card {t}"><div class="kl">Avg Latency</div><div class="kv" style="color:{vc}">{avg_lat} ms</div><div class="ks">Порог: &lt; 3000 ms</div></div>',
                unsafe_allow_html=True,
            )
        with d2:
            t = "warn-t" if fb_pct >= 20 else "ok-t"
            vc = "#f59e0b" if fb_pct >= 20 else "#10b981"
            st.markdown(
                f'<div class="kpi-card {t}"><div class="kl">Fallback Rate</div><div class="kv" style="color:{vc}">{fb_pct:.1f}%</div><div class="ks">Порог: &lt; 20%</div></div>',
                unsafe_allow_html=True,
            )
        with d3:
            t = "err-t" if s["error_count"] > 0 else "ok-t"
            vc = "#ef4444" if s["error_count"] > 0 else "#10b981"
            st.markdown(
                f'<div class="kpi-card {t}"><div class="kl">API Errors</div><div class="kv" style="color:{vc}">{s["error_count"]}</div><div class="ks">Должно быть 0</div></div>',
                unsafe_allow_html=True,
            )

        # ── FAQ Gap Analysis ───────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label">🔍 FAQ Gap Analysis — что добавить в базу знаний</div>',
            unsafe_allow_html=True,
        )
        gaps = [e["question"] for e in s["questions_log"] if e["is_fallback"]]
        if gaps:
            for g in gaps:
                st.markdown(
                    f'<div class="gap-pill">❓ {g}'
                    f'<div class="rec">→ Рекомендация: добавьте ответ в faq.txt</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="health-ok">✅ Пробелов не обнаружено — FAQ полностью покрывает все вопросы этой сессии.</div>',
                unsafe_allow_html=True,
            )

        # ── FinOps table ───────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-label">💰 FinOps — детализация по запросам</div>',
            unsafe_allow_html=True,
        )
        user_msgs = [m for m in s["chat_history"] if m["role"] == "user"]
        bot_msgs = [m for m in s["chat_history"] if m["role"] == "assistant"]
        rows = []
        for i, (u, b) in enumerate(zip(user_msgs, bot_msgs), 1):
            meta = b.get("meta", {})
            rows.append(
                {
                    "#": i,
                    "Вопрос": u["content"][:50]
                    + ("…" if len(u["content"]) > 50 else ""),
                    "Статус": "⚠️ Fallback"
                    if meta.get("is_fallback")
                    else "✅ Answered",
                    "In tok": meta.get("input_tokens", 0),
                    "Out tok": meta.get("output_tokens", 0),
                    "Cost $": f"{usd_cost(meta.get('input_tokens', 0), meta.get('output_tokens', 0)):.5f}",
                    "Latency ms": meta.get("latency_ms", 0),
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
