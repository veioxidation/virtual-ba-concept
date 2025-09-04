def generate_advisory(state: dict) -> dict:
    """
    Tool to generate advisory recommendations based on process analysis.
    """
    user_input = state["user_input"]
    process_report = state["process_report"]
    calculated_metrics = state["calculated_metrics"]
    
    # Analyze process for improvement opportunities
    recommendations = []
    
    # Check process efficiency
    if calculated_metrics.get("average_step_duration", 0) > 10:
        recommendations.append("Consider optimizing steps with long durations to improve overall efficiency")
    
    # Check process complexity
    total_steps = calculated_metrics.get("total_steps", 0)
    if total_steps > 15:
        recommendations.append("Process appears complex - consider breaking down into sub-processes")
    elif total_steps < 3:
        recommendations.append("Process may be oversimplified - ensure all necessary steps are captured")
    
    # Check for bottlenecks
    process_steps = process_report.get("process_steps", [])
    if process_steps:
        max_duration_step = max(process_steps, key=lambda x: x.get("duration", 0))
        if max_duration_step.get("duration", 0) > 20:
            recommendations.append(f"Potential bottleneck identified in step: {max_duration_step.get('name', 'Unknown')}")
    
    # Check for missing automation opportunities
    manual_steps = [step for step in process_steps if step.get("automation_level", "manual") == "manual"]
    if len(manual_steps) > len(process_steps) * 0.7:
        recommendations.append("High proportion of manual steps - explore automation opportunities")
    
    # Generate response
    if recommendations:
        answer = "Based on my analysis, here are my advisory recommendations:\n\n" + \
                "\n".join([f"• {rec}" for rec in recommendations]) + \
                "\n\nWould you like me to elaborate on any of these recommendations?"
    else:
        answer = "The process appears well-optimized based on current data. Continue monitoring performance and consider periodic reviews."
    
    return {"conversation_history": {"role": "assistant", "content": answer}, "advisory_recommendations": recommendations} 