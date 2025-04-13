def generate_questions_prompt(topic: str, group: dict) -> str:
    roles_context = "\n".join([f"- {p['name']}: {p['role']}" for p in group.get("participants", [])])

    prompt = (
        f"You are a meeting moderator conducting a discussion on '{topic}' with the following participants:\n"
        f"{roles_context}\n\n"
        f"Group Context: {group.get('context', 'No additional context provided')}\n\n"
        f"Generate 10 questions that the participants needs to discuss to get an agreement about {topic}."
        f"The questions should not be targetted at a specific user."
        f"List them as:\n1. b\n2. \n3. \n4. \n5. \n6. "
    )

    return prompt
