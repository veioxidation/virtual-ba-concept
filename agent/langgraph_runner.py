from langgraph.graph import StateGraph, END
from agent.state_schema import VirtualBAState
from agent.router import route_user_input
from agent.decider import decide_next_tool
from agent.tools import (
    query_qa,
    fill_knowledge_gap,
    calculate_metrics,
    generate_advisory,
)




def build_graph():
    workflow = StateGraph(VirtualBAState)

    # Add all nodes
    workflow.add_node("router", route_user_input)
    workflow.add_node("query_qa", query_qa)
    workflow.add_node("fill_gap", fill_knowledge_gap)
    workflow.add_node("metrics", calculate_metrics)
    workflow.add_node("advisory", generate_advisory)
    workflow.add_node("tool_or_finish", decide_next_tool)

    # Entry point
    workflow.set_entry_point("router")

    # First router decision
    workflow.add_conditional_edges(
        "router",
        lambda state: state["route"],
        {
            "query": "query_qa",
            "fill_gap": "fill_gap",
            "metrics": "metrics",
            "advisory": "advisory",
        }
    )

    # Tool chaining: after each tool → decision
    for tool in ["query_qa", "fill_gap", "metrics", "advisory"]:
        workflow.add_edge(tool, "tool_or_finish")

    # tool_or_finish makes another decision or ends
    workflow.add_conditional_edges(
        "tool_or_finish",
        lambda state: state["route"],
        {
            "query": "query_qa",
            "fill_gap": "fill_gap",
            "metrics": "metrics",
            "advisory": "advisory",
            "finish": END,
        }
    )

    return workflow.compile()
