from agent.state_schema import VirtualBAState

def fill_knowledge_gap(state: VirtualBAState) -> dict:
    """
    Tool to identify and fill knowledge gaps in the process analysis.
    """
    user_input = state.user_input
    process_report = state.process_report
    
    # Analyze the process report to identify gaps
    gaps_identified = []
    
    # Check for missing process steps
    if not process_report.get("process_steps"):
        gaps_identified.append("Process steps not documented")
    
    # Check for missing metrics
    if not process_report.get("metrics"):
        gaps_identified.append("Performance metrics not available")
    
    # Check for missing stakeholder information
    if not process_report.get("stakeholders"):
        gaps_identified.append("Stakeholder roles not defined")
    
    # Generate response
    if gaps_identified:
        answer = f"I've identified the following knowledge gaps:\n" + \
                "\n".join([f"• {gap}" for gap in gaps_identified]) + \
                "\n\nWould you like me to help gather this information?"
    else:
        answer = "The process documentation appears complete. No significant knowledge gaps identified."
    
    return {"conversation_history": {"role": "assistant", "content": answer}} 