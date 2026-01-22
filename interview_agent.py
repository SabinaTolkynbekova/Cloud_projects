import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Load environment variables
load_dotenv()

def configure_genai():
    """Configures the Gemini API."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print(Fore.RED + "Error: GOOGLE_API_KEY not found in environment variables.")
        print(Fore.YELLOW + "Please set it in a .env file or export it.")
        sys.exit(1)
    genai.configure(api_key=api_key)

class ProductInterviewAgent:
    def __init__(self, model_name='gemini-1.5-flash-latest'):
        self.model = genai.GenerativeModel(model_name)
        self.chat = self.model.start_chat(history=[])
        self.conversation_history = []

    def start_interview(self):
        """Conducts the interview using the 5 Whys technique."""
        print(Fore.CYAN + "\n=== Gemini Product Manager Agent ===")
        print(Fore.GREEN + "Hello! I'm here to help you define your product requirements.")
        print("I'll ask you a few questions to understand the root problem better.\n")

        # Initial context setting for the model
        system_instruction = (
            "You are an expert Product Manager using the 'Jobs to be Done' (JTBD) framework and '5 Whys' technique. "
            "Your goal is to interview a user to uncover the underlying 'Job' they are hiring the product to do. "
            "You must ask deep, probing 'Why' questions to get to the root cause. "
            "Do not settle for superficial answers. "
            "Start by asking about the product idea or problem. "
            "Then, recursively ask 'Why' to understand the motivation, context, and desired outcome."
        )
        
        # We inject the system instruction implicitly
        self.conversation_history.append(f"System: {system_instruction}")
        
        # Step 1: Initial Question
        initial_question = "To start, what is the product idea or the problem you are trying to solve?"
        print(Fore.BLUE + "Agent: " + Style.RESET_ALL + initial_question)
        self.conversation_history.append(f"Agent: {initial_question}")
        
        user_input = input(Fore.YELLOW + "You: " + Style.RESET_ALL)
        self.conversation_history.append(f"User: {user_input}")

        # Step 2: Loop for 5 Whys (approx 5 rounds)
        for i in range(5):
            prompt = (
                f"The user just said: '{user_input}'. "
                "Previous conversation context is implied. "
                "Ask a specific 'Why' question to dig deeper into the user's motivation or the root problem. "
                "Use the '5 Whys' technique. "
                "Example: 'Why is that important to you?' or 'Why does this problem occur?' "
                "Ensure the question relates to the 'Job to be Done'."
            )
            
            response = self.chat.send_message(prompt)
            question = response.text.strip()
            
            print(Fore.BLUE + f"Agent ({i+1}/5): " + Style.RESET_ALL + question)
            self.conversation_history.append(f"Agent: {question}")
            
            user_input = input(Fore.YELLOW + "You: " + Style.RESET_ALL)
            self.conversation_history.append(f"User: {user_input}")
            
            if user_input.lower() in ['exit', 'quit', 'done']:
                print(Fore.MAGENTA + "Ending interview early...")
                break

    def generate_prd(self):
        """Generates the PRD based on the interview history."""
        print(Fore.CYAN + "\nGenerating Product Requirements Document (PRD)... Please wait.")
        
        transcript = "\n".join(self.conversation_history)
        
        prd_prompt = (
            "Based on the following interview transcript, write a comprehensive "
            "Product Requirements Document (PRD) in Markdown format.\n\n"
            "TRANSCRIPT:\n"
            f"{transcript}\n\n"
            "REQUIREMENTS:\n"
            "1. Title & Overview\n"
            "2. Problem Statement (Root Cause Analysis)\n"
            "3. Goals & Success Metrics\n"
            "4. User Personas\n"
            "5. User Stories\n"
            "6. Functional Requirements\n"
            "7. Non-functional Requirements\n"
            "8. Output strictly in Markdown."
        )
        
        response = self.model.generate_content(prd_prompt)
        return response.text

    def save_prd(self, content, filename="PRD.md"):
        try:
            with open(filename, "w", encoding='utf-8') as f:
                f.write(content)
            print(Fore.GREEN + f"\nSuccess! PRD saved to {filename}")
        except Exception as e:
            print(Fore.RED + f"Error saving file: {e}")

def main():
    configure_genai()
    
    agent = ProductInterviewAgent()
    try:
        agent.start_interview()
        prd_content = agent.generate_prd()
        agent.save_prd(prd_content)
    except KeyboardInterrupt:
        print(Fore.RED + "\nProcess interrupted.")
    except Exception as e:
        print(Fore.RED + f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
