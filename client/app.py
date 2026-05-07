import httpx
import chainlit as cl

API_URL = "http://localhost:8000"


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("session_id", cl.context.session.id)
    await cl.Message(content="Hello! Ask me anything about League of Legends.").send()


@cl.on_message
async def on_message(message: cl.Message):
    session_id = cl.user_session.get("session_id")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{API_URL}/query",
            json={"query": message.content, "session_id": session_id},
        )
        response.raise_for_status()
        data = response.json()

    answer = data["answer"]
    sources = data.get("sources", [])

    msg = cl.Message(content=answer)

    if sources:
        source_text = "\n".join(f"- {s}" for s in sources)
        msg.content += f"\n\n**Sources:**\n{source_text}"

    await msg.send()
