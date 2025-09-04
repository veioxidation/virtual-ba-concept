from agent.model.model import model

def route_user_input(state: dict) -> dict:
    question = state["user_input"]

    system_prompt = """
    You are an intelligent assistant analyzing business processes.
    Decide what the user is trying to do:

    Choices:
    - "query": ask about the process
    - "fill_gap": respond to a question from the generated report
    - "metrics": calculate process metrics
    - "advisory": ask for suggestions/improvements
    """

    completion = model.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ])

    return {**state, "route": completion.content.strip()}
