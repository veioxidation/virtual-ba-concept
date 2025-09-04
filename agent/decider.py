from agent.model.model import model

def decide_next_tool(state: dict) -> dict:
    history = state["conversation_history"]
    system_prompt = """
You are a process assistant. Based on the full history of the conversation, decide what to do next.

Available options:
- "query": user still wants answers about the process
- "fill_gap": user wants to clarify something in the report
- "metrics": user wants more structural metrics
- "advisory": user seeks suggestions
- "finish": end the session with a final answer
"""

    messages = [{"role": "system", "content": system_prompt}] + history

    result = model.invoke(messages)

    return {
        **state,
        "route": result.content.strip(),
        "conversation_history": history + [{"role": "assistant", "content": result.content.strip()}]
    }
