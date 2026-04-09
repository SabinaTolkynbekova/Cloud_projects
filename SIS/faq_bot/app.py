import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

SYSTEM_PROMPT_FILE = "system_prompt.txt"


def load_system_prompt() -> str:
    """Load the system prompt from a text file."""
    try:
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return ""


def get_answer(api_key: str, question: str, faq_content: str, system_prompt_template: str) -> str:
    """Send question + FAQ context to Gemini and return the answer."""
    try:
        genai.configure(api_key=api_key)

        system_instruction = system_prompt_template.replace("{faq_content}", faq_content)

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction,
            generation_config=genai.GenerationConfig(
                temperature=0.0
            )
        )

        response = model.generate_content(question)

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return "Уточните у администратора"

    except Exception as e:
        return f"Техническая ошибка (для отладки): {str(e)}"
        
def main():
    st.set_page_config(page_title="FAQ Bot", page_icon="🤖", layout="centered")

    st.title("FAQ Support Assistant 🤖")
    st.markdown(
        "Upload a text file with your FAQ content and ask questions in **Russian** or **Kazakh**."
    )

    # Try loading API key from .env first
    env_api_key = os.getenv("GEMINI_API_KEY")

    # Sidebar input for manual fallback
    manual_api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")

    # Final API key
    api_key = env_api_key if env_api_key else manual_api_key

    # Show key status
    if env_api_key:
        st.sidebar.success("Gemini API key loaded from .env")
    elif manual_api_key:
        st.sidebar.success("Gemini API key entered manually")
    else:
        st.sidebar.warning("No Gemini API key found yet")

    if not api_key:
        st.warning("Please add your Gemini API key in `.env` or enter it in the sidebar to continue.")
        st.stop()

    # Upload FAQ file
    uploaded_file = st.file_uploader("Upload your FAQ text file (.txt)", type=["txt"])

    if uploaded_file is not None:
        try:
            faq_content = uploaded_file.read().decode("utf-8").strip()
        except Exception:
            st.error("Could not read the file. Please upload a valid UTF-8 .txt file.")
            st.stop()

        if not faq_content:
            st.error("The uploaded FAQ file is empty.")
            st.stop()

        st.success("FAQ file uploaded successfully!")

        # User question
        user_question = st.text_input("Ask your question:")

        if st.button("Get Answer"):
            if not user_question.strip():
                st.error("Please enter a question.")
                st.stop()

            system_prompt_template = load_system_prompt()

            if not system_prompt_template:
                st.error("system_prompt.txt not found or empty. Please make sure it exists in the project folder.")
                st.stop()

            with st.spinner("Thinking..."):
                answer = get_answer(
                    api_key=api_key,
                    question=user_question,
                    faq_content=faq_content,
                    system_prompt_template=system_prompt_template
                )

            st.markdown("### Answer:")
            st.info(answer)


if __name__ == "__main__":
    main()