import os
from dotenv import load_dotenv
from openclaw.core import Assistant
from openclaw.providers.groq import GroqProvider  # Correct import for 2026
from openclaw.memory import FileBufferMemory

load_dotenv()
def bot_factory(model_name="groq/llama-3.3-70b-versatile"):
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise ValueError("❌ GROQ_API_KEY is missing from your .env file!")

    # Step: Initialize the Groq provider
    # Note: Ensure the model string matches Groq's current catalog
    provider = GroqProvider(
        api_key=api_key,
        model_id=model_name,
        temperature=0.7,
        max_tokens=4096
    )

    # Step: Attach memory (essential for OpenClaw-Bot persistence)
    memory = FileBufferMemory(storage_path="./sessions")

    return Assistant(
        provider=provider,
        memory=memory,
        name="ClawAgent"
    )
# In your main execution file:
try:
    bot = bot_factory()
    print("🚀 OpenClaw-Bot is live using Groq LPU™ inference.")
    bot.run()
except Exception as e:
    print(f"Failed to start bot: {e}")