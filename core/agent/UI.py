from agent import LLMAgent
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()

    llm_agent = LLMAgent()
    llm_agent.start_new_turn()
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting the conversation.")
            break
        
        response = llm_agent.get_response(user_input)
        print("Agent:", response)