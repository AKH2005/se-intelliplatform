from app.services.intent_router import IntentRouter

queries = [
    "Add a login page to my application.",
    "Improve the login page design.",
    "Add a forgot password link.",
    "Make the login page responsive.",
    "Explain how authentication works.",
]

for q in queries:
    res = IntentRouter.classify(q)
    print(f"Query: '{q}' -> Intent: {res.intent.value}, Persona: {res.persona}, AllowActions: {res.allow_actions}")
