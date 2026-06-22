# middlewares/compression.py

import tiktoken
from langchain.agents.middleware import before_model
from langchain_openai import ChatOpenAI

# Token counter
enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages):
    total = 0
    for m in messages:
        total += len(enc.encode(m["content"]))
    return total


@before_model
def compression_middleware(state, inputs):
    """
    Auto compression middleware for LangChain agent.
    - Detects context overflow
    - Generates memory summary using gpt-4.1-mini
    - Rewrites messages into compressed history
    """
    print(state)
    print(inputs)

    # msgs = inputs["messages"]

    # # token tracking: expect agent state to contain tracked usage
    
    # used_tokens = state.get("token_used", 0)
    # token_limit = state.get("token_limit", 128000)
    # threshold = state.get("token_threshold", 0.8)

    # print(f"[middleware:compression] Used={used_tokens} Limit={token_limit}")

    # if used_tokens < token_limit * threshold:
    #     return inputs  # skip compression

    # print("[middleware:compression] ⚠ Triggering compression...")

    # mini_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

    # summary_prompt = [
    #     {"role": "system", "content": "Summarize previous messages into concise persistent memory"},
    #     *msgs
    # ]

    # summary_resp = mini_llm.invoke({"messages": summary_prompt})
    # summary_text = summary_resp["messages"][-1].content

    # # rebuild compressed window
    # compressed_msgs = [
    #     {"role": "system", "content": "Conversation summary: " + summary_text}
    # ]

    # # keep last 20 messages
    # if len(msgs) > 20:
    #     compressed_msgs.extend(msgs[-20:])
    # else:
    #     compressed_msgs.extend(msgs)

    # inputs["messages"] = compressed_msgs
    # print("[middleware:compression] ✔ Compression finished")

    return inputs
