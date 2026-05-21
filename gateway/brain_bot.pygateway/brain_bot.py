"""
OpenClaw — gateway/brain_bot.py
THE MAIN BRAIN — Conversational Discord bot.
Talk to it naturally. It decomposes your task, spawns agents,
shows live progress embeds, and posts the full result back to Discord.
"""
import os, asyncio, json, time, traceback
import discord
from discord import app_commands
from dotenv import load_dotenv
from worker.ai_worker import orchestrate_task, process_task, AGENT_PERSONAS
from worker.executor import ExecutorEngine
from worker.task_router import TaskRouter
from memory import init_db, save_task, update_task, get_stats, get_recent_tasks

load_dotenv()

DISCORD_TOKEN  = os.environ["DISCORD_TOKEN"]
BRAIN_CHANNEL  = os.environ.get("BRAIN_CHANNEL", "")
BOT_PREFIX     = os.environ.get("BOT_PREFIX", "brain")

CLR_THINKING = 0xf5a623
CLR_RUNNING  = 0x0099ff
CLR_DONE     = 0x00d26a
CLR_FAIL     = 0xff3b30
CLR_TEST     = 0x9b59b6

AGENT_EMOJI = {
    "orchestrator": "\U0001f9e0", "coder": "\U0001f468\u200d\U0001f4bb", "reviewer": "\U0001f50d",
    "qa": "\U0001f9ea", "ops": "\U0001f680", "research": "\U0001f4e1",
    "growth": "\U0001f4c8", "memory": "\U0001f4be", "github": "\U0001f419",
    "browser": "\U0001f310",
}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds          = True


class BrainBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree     = app_commands.CommandTree(self)
        self.executor = ExecutorEngine()
        self.router   = TaskRouter()

    async def setup_hook(self):
        await self.tree.sync()
        print("[BrainBot] Slash commands synced")

    async def on_ready(self):
        init_db()
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="your commands | just talk to me"
            )
        )
        print(f"[BrainBot] Online as {self.user} | Brain channel: '{BRAIN_CHANNEL}'")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        content = message.content.strip()
        is_mention  = self.user in message.mentions
        in_brain_ch = BRAIN_CHANNEL and message.channel.name == BRAIN_CHANNEL
        if not is_mention and not in_brain_ch:
            return
        if is_mention:
            content = content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()
        if not content:
            await message.channel.send(
                embed=discord.Embed(
                    title="\U0001f9e0 BrainBot Ready",
    async def _handle_task(self, message: discord.Message, task: str):
        channel = message.channel
        thinking_embed = discord.Embed(
            title="\U0001f9e0 MAIN BRAIN \u2014 Analysing Task",
            description=f"**Task:** {task[:300]}",
            color=CLR_THINKING,
        )
        thinking_embed.add_field(name="Status", value="Decomposing into agent plan\u2026", inline=False)
        thinking_embed.set_footer(text=f"OpenClaw | {_ts()}")
        status_msg = await channel.send(embed=thinking_embed)
        try:
            route    = await asyncio.get_event_loop().run_in_executor(None, lambda: self.router.route(task))
            plan_raw = await asyncio.get_event_loop().run_in_executor(None, lambda: orchestrate_task(task))
            plan     = json.loads(plan_raw)
        except Exception:
            plan  = [{"agent": "orchestrator", "task": task}]
            route = {"needs_browser": False}
        needs_browser = route.get("needs_browser", False)
        valid_plan    = [p for p in plan if p.get("agent") in AGENT_PERSONAS or p.get("agent") == "browser"]
        plan_embed = discord.Embed(
            title="\U0001f9e0 MAIN BRAIN \u2014 Swarm Activated",
            description=f"**Task:** {task[:300]}",
            color=CLR_RUNNING,
        )
        agent_lines = "\n".join(
            f"{AGENT_EMOJI.get(p['agent'], '\U0001f916')} **{p['agent'].upper()}** \u2014 {p['task'][:80]}"
            for p in valid_plan
        )
        plan_embed.add_field(name=f"Execution Plan ({len(valid_plan)} agents)", value=agent_lines or "orchestrator", inline=False)
        if needs_browser:
            plan_embed.add_field(name="\U0001f310 Web Execution", value="Browser agent will execute real web tasks", inline=True)
        plan_embed.set_footer(text=f"OpenClaw | {_ts()}")
        await status_msg.edit(embed=plan_embed)
        results        = {}
        agent_statuses = {p["agent"]: "Running\u2026" for p in valid_plan}
        async def run_one(agent_name: str, agent_task: str):
            try:
                if agent_name == "browser" and needs_browser:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self.executor.run_browser(agent_task, task)
                    )
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: process_task(agent_task, agent_name)
                    )
                results[agent_name]        = result
                agent_statuses[agent_name] = "Done"
            except Exception as e:
                results[agent_name]        = f"ERROR: {e}"
                agent_statuses[agent_name] = "Failed"
            await _update_live_embed(status_msg, task, agent_statuses, valid_plan)
        await asyncio.gather(*[run_one(p["agent"], p["task"]) for p in valid_plan])
        for p in valid_plan:
            agent   = p["agent"]
            out     = results.get(agent, "No output")
            preview = out[:900] + "\u2026" if len(out) > 900 else out
            embed   = discord.Embed(
                title=f"{AGENT_EMOJI.get(agent,'\U0001f916')} {agent.upper()} \u2014 Complete",
                description=f"```{preview}```",
                color=CLR_DONE if "ERROR" not in out else CLR_FAIL,
            )
            embed.set_footer(text=f"OpenClaw | {_ts()}")
            await channel.send(embed=embed)
        qa_result  = await asyncio.get_event_loop().run_in_executor(None, lambda: self.executor.self_test(task, results))
        qa_verdict = "PASSED" if qa_result.get("passed") else "FAILED"
        qa_embed   = discord.Embed(title=f"\U0001f9ea QA \u2014 {qa_verdict}", description=qa_result.get("summary", ""), color=CLR_TEST)
        qa_embed.add_field(name="Tests Run",    value=str(qa_result.get("tests_run",    0)), inline=True)
        qa_embed.add_field(name="Tests Passed", value=str(qa_result.get("tests_passed", 0)), inline=True)
        qa_embed.set_footer(text=f"OpenClaw QA | {_ts()}")
        await channel.send(embed=qa_embed)

client = BrainBot()
tree   = client.tree


@tree.command(name="brain", description="\U0001f9e0 Talk to the MAIN BRAIN")
@app_commands.describe(task="What do you want done?")
async def brain_cmd(itx: discord.Interaction, task: str):
    await itx.response.defer(thinking=True)
    await client._handle_task(itx, task)
    await itx.followup.send("Task pipeline complete.")


@tree.command(name="status", description="\U0001f4ca Live swarm status")
async def status_cmd(itx: discord.Interaction):
    s = get_stats()
    r = get_recent_tasks(5)
    e = discord.Embed(title="\U0001f4ca OpenClaw Swarm Status", color=0x0099ff)
    e.add_field(name="Total Tasks", value=str(s.get("total_tasks", 0)), inline=True)
    e.add_field(name="Done",        value=str(s.get("done",        0)), inline=True)
    e.add_field(name="Failed",      value=str(s.get("failed",      0)), inline=True)
    if r:
        lines = "\n".join(f"`{t['id']}` **{t['agent']}** [{t['status']}] {t['desc'][:50]}" for t in r)
        e.add_field(name="Recent", value=lines, inline=False)
    e.set_footer(text=f"OpenClaw | {_ts()}")
    await itx.response.send_message(embed=e)


@tree.command(name="agents", description="\U0001f916 List all swarm agents")
async def agents_cmd(itx: discord.Interaction):
    e = discord.Embed(title="\U0001f916 Swarm Agents", color=0x9b59b6)
    for name, desc in AGENT_PERSONAS.items():
        e.add_field(name=f"{AGENT_EMOJI.get(name,'\U0001f916')} {name.upper()}", value=desc[:100], inline=False)
    e.set_footer(text="Use /brain or talk in #brain | OpenClaw")
    await itx.response.send_message(embed=e)


@tree.command(name="stop", description="\U0001f6d1 Emergency stop")
async def stop_cmd(itx: discord.Interaction):
    e = discord.Embed(title="\U0001f6d1 STOP ACKNOWLEDGED", description="All running operations flagged.\nRailway: `railway down`", color=0xff0000)
    await itx.response.send_message(embed=e)


def _ts() -> str:
    return time.strftime("%H:%M:%S UTC", time.gmtime())


async def _update_live_embed(msg, task, statuses, plan):
    lines = "\n".join(
        f"{AGENT_EMOJI.get(p['agent'],'\U0001f916')} **{p['agent'].upper()}** \u2014 {statuses.get(p['agent'],'Queued')}"
        for p in plan
    )
    e = discord.Embed(
        title="\U0001f9e0 MAIN BRAIN \u2014 Agents Running",
        description=f"**Task:** {task[:200]}",
        color=CLR_RUNNING,
    )
    e.add_field(name="Agent Progress", value=lines, inline=False)
    e.set_footer(text=f"OpenClaw | Live | {_ts()}")
    try:
        await msg.edit(embed=e)
    except Exception:
        pass


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)

        final_embed = discord.Embed(title="\U0001f3c1 Task Complete", description=f"**Task:** {task[:200]}", color=CLR_DONE)
        final_embed.add_field(name="Agents Run", value=str(len(valid_plan)), inline=True)
        final_embed.add_field(name="QA",         value=qa_verdict,          inline=True)
        final_embed.set_footer(text=f"OpenClaw | {_ts()}")
        await channel.send(embed=final_embed)
        summary_text = "\n\n".join(f"**{p['agent'].upper()}:**\n{results.get(p['agent'],'')[:300]}" for p in valid_plan)
        asyncio.get_event_loop().run_in_executor(None, lambda: self.executor.post_slack(task, summary_text, qa_result))
        asyncio.get_event_loop().run_in_executor(None, lambda: self.executor.post_github_issue(task, summary_text))

                    description=(
                        "Tell me **anything** — I'll break it into agent tasks and execute hands-free.\n\n"
                        "**Examples:**\n"
                        "- build me a Shopify store for selling sneakers\n"
                        "- create a Python API that tracks crypto prices\n"
                        "- deploy a new Railway service called auth-service\n"
                    ),
                    color=CLR_DONE,
                ).set_footer(text="OpenClaw Swarm OS")
            )
            return
        await self._handle_task(message, content)
