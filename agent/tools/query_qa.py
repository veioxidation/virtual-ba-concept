def query_qa(state: dict) -> dict:
    user_question = state["user_input"]
    process_report = state["process_report"]
    
    # For now just a dummy response
    answer = f"Here's what I found about the process: [stub for: {user_question}]"

    return {"conversation_history": {"role": "assistant", "content": answer}}
