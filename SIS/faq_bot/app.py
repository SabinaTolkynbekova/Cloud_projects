import streamlit as st
import anthropic
import os
from dotenv import load_dotenv

# Load environment variables, e.g., ANTHROPIC_API_KEY if placed in a .env file
load_dotenv()

SYSTEM_PROMPT_FILE = "system_prompt.txt"

def load_system_prompt() -> str:
    """Loads the system prompt reading it from the text file."""
    try:
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "system_prompt.txt not found. Please ensure it is in the same directory."

def get_answer(api_key: str, question: str, faq_content: str, system_prompt_temp: str) -> str:
    """Sends the user question and the FAQ content to Anthropic API."""
    try:
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Inject the FAQ content into the system prompt template
        system_prompt = system_prompt_temp.replace("{faq_content}", faq_content)
        
        # Call the Anthropic Messages API
        # Using claude-3-haiku for fast and cost-effective text tasks, or sonnet if needed
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": question}
            ],
            temperature=0  # Low temperature strictly for factual retrieval
        )
        
        # Return the extracted text answer
        return response.content[0].text
    except Exception as e:
        return f"Error communicating with Anthropic API: {str(e)}"

def main():
    # Setup standard Streamlit configuration
    st.set_page_config(page_title="FAQ Bot", page_icon="🤖", layout="centered")
    st.title("FAQ Support Assistant 🤖")
    
    st.markdown("""
    Upload a text file with your FAQ content and ask questions in **Russian** or **Kazakh**.
    """)
    
    # 1. Provide an option for the API Key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = st.sidebar.text_input("Enter your Anthropic API Key", type="password")
        if not api_key:
            st.warning("Please enter your Anthropic API Key in the sidebar to continue.")
            return

    # 2. File uploader for the FAQ content
    uploaded_file = st.file_uploader("Upload your FAQ text file (.txt)", type=["txt"])
    
    if uploaded_file is not None:
        # Decode uploaded bytes to string
        faq_content = uploaded_file.read().decode("utf-8")
        st.success("FAQ file uploaded successfully!")
        
        # 3. User question input
        user_question = st.text_input("Ask your question:")
        
        if st.button("Get Answer"):
            if not user_question.strip():
                st.error("Please enter a question.")
            else:
                with st.spinner("Thinking..."):
                    # Load the instructions for the LLM
                    system_prompt_temp = load_system_prompt()
                    
                    if "not found" in system_prompt_temp:
                        st.error(system_prompt_temp)
                        return
                        
                    # Request answer
                    answer = get_answer(
                        api_key=api_key,
                        question=user_question,
                        faq_content=faq_content,
                        system_prompt_temp=system_prompt_temp
                    )
                    
                    # Display the final answer
                    st.markdown("### Answer:")
                    st.info(answer)

if __name__ == "__main__":
    main()
