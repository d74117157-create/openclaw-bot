import os
import discord
from discord import app_commands
from discord.ext import commands
from groq import Groq

# ============================
#  CONFIG
# ============================

TOKEN = os.environ.get("DISCORD_WORKER_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Change this per worker bot:
# writer, researcher, designer, automation, etc.
ROLE_NAME = os.environ.get("WORKER_ROLE", "writer")

intents = discord.Intents.default()
intents.message_content = False

bot = commands.Bot(command_prefix="!", intents=intents)

groq_client = Groq(api_key=GROQ_API_KEY)

# ============================
#  SYSTEM PROMPT
# ============================

SYSTEM_PROMPT = (
    f"You are an OpenClaw worker bot with role '{ROLE_NAME}'. "
    "You receive execution tasks from a central Planner. "
    "You do NOT plan, you EXECUTE. "
    "You take 'action' and 'payload' and produce the best possible result. "
    "Be concrete, useful, and production-ready. "
    "Use Discord-friendly formatting (markdown, code blocks, etc)."
)

# ============================
#  LLM EXECUTION
# ============================

def run_worker_llm(action: str, payload: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Action: {action}\n\n"
                f"Payload:\n{payload}\n\n"
                "Execute this task fully and return the final result."
            ),
        },
    ]

    resp = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        max_tokens=1200,
    )

    return resp.choices[0].message.content

# ============================
#  DISCORD EVENTS
# ============================

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"[Worker:{ROLE_NAME}] Slash commands synced")
    except Exception as e:
        print(f"[Worker:{ROLE_NAME}] Error syncing commands: {e}")

    print(f"[Worker:{ROLE_NAME}] {bot.user} online and ready to execute tasks.")

# ============================
#  /execute COMMAND
# ============================

@bot.tree.command(name="execute", description="Execute a remote swarm task.")
@app_commands.describe(
    action="The action name (e.g., create_product_outline, write_email_sequence)",
    payload="The payload or instructions for this action",
)
async def execute(interaction: discord.Interaction, action: str, payload: str):
    await interaction.response.defer(thinking=True)

    try:
        result = run_worker_llm(action, payload)
    except Exception as e:
        result = f"Error while executing task: {e}"

    await interaction.followup.send(result)

# ============================
#  RUN BOT
# ============================

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_WORKER_BOT_TOKEN not set.")
    elif not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set.")
    else:
        bot.run(TOKEN)