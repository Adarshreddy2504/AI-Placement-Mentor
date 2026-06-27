def choose_model(prompt):

    prompt = prompt.lower()

    hard_keywords = [
        "python",
        "java",
        "html",
        "css",
        "javascript",
        "react",
        "sql",
        "database",
        "algorithm",
        "code",
        "project",
        "debug",
        "design"
    ]

    if len(prompt) > 150:
        return "llama-3.3-70b-versatile"

    for word in hard_keywords:
        if word in prompt:
            return "llama-3.3-70b-versatile"

    return "llama-3.1-8b-instant"