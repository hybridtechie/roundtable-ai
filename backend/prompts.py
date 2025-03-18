def generate_questions_prompt(topic: str, group: dict) -> str:
    roles_context = "\n".join([f"- {p['name']}: {p['role']}" for p in group.get("participants", [])])
    
    prompt = (
        f"You are a meeting moderator conducting a discussion on '{topic}' with the following participants:\n"
        f"{roles_context}\n\n"
        f"Group Context: {group.get('context', 'No additional context provided')}\n\n"
        f"Generate 10 targeted questions that will engage these specific participants in a meaningful discussion about {topic}."
    )
    
    return prompt