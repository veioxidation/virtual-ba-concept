def calculate_metrics(state: dict) -> dict:
    """
    Tool to calculate and analyze process performance metrics.
    """
    user_input = state["user_input"]
    process_report = state["process_report"]
    
    # Extract process data for calculations
    process_steps = process_report.get("process_steps", [])
    historical_data = process_report.get("historical_data", {})
    
    # Calculate basic metrics
    metrics = {}
    
    if process_steps:
        # Process efficiency metrics
        total_steps = len(process_steps)
        avg_duration = sum(step.get("duration", 0) for step in process_steps) / total_steps if total_steps > 0 else 0
        
        metrics["total_steps"] = total_steps
        metrics["average_step_duration"] = round(avg_duration, 2)
        metrics["total_process_time"] = sum(step.get("duration", 0) for step in process_steps)
    
    if historical_data:
        # Historical performance metrics
        completion_times = historical_data.get("completion_times", [])
        if completion_times:
            metrics["avg_completion_time"] = round(sum(completion_times) / len(completion_times), 2)
            metrics["min_completion_time"] = min(completion_times)
            metrics["max_completion_time"] = max(completion_times)
    
    # Generate response
    if metrics:
        answer = "Here are the calculated process metrics:\n\n" + \
                "\n".join([f"• **{key.replace('_', ' ').title()}**: {value}" for key, value in metrics.items()])
    else:
        answer = "Unable to calculate metrics due to insufficient process data. Please ensure process steps and historical data are available."
    
    return {"conversation_history": {"role": "assistant", "content": answer}, "calculated_metrics": metrics} 