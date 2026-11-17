import asyncio
import uuid
from app.services.intent_router import IntentRouter
from app.services.assistant_reasoning_service import AssistantReasoningService

async def main():
    service = AssistantReasoningService()
    query = "Explain how authentication works."
    classification = IntentRouter.classify(query)
    print("Classification:", classification.intent, classification.allow_actions)

    chunks = []
    async for chunk in service.generate_response_stream(
        user_message=query,
        context=None,
        history_messages=[],
        classification=classification,
    ):
        chunks.append(chunk)

    full_resp = "".join(chunks)
    print("Response length:", len(full_resp))
    print("Response preview:\n", full_resp[:400])

if __name__ == "__main__":
    asyncio.run(main())
