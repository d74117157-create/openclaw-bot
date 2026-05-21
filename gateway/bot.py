"""
OpenClaw — gateway/bot.py
Primary Discord gateway. All slash commands + MAIN BRAIN orchestration.
"""
import os, asyncio, json
import discord
from discord import app_commands
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from memory import init_db, save_task, update_task, get_stats, get_recent_tasks, get_failed_tasks, save_decision
from worker.ai_worker import process_task, orchestrate_task, multi_agent_pipeline, AGENT_PERSONAS

load_dotenv()

DISCORD_TOKEN  = os.environ["DISCORD_TOKEN"]
SLACK_BOT_TOKEN= os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL  = os.environ.get("SLACK_CHANNEL", "openclaw-ops")
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO    = os.environ.get("GITHUB_REPO", "")   # owner/repo

slack = WebClient(token=SLACK_BOT_TOKEN)


# -- Slack helper --
def post_slack(agent: str, task_desc: str, result: str, status: str = "OK"):
    if not SLACK_BOT_TOKEN:
        return
    try:
        preview = result[:2800]
        slack.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=[
                {"type": "header",
                 "text": {"type": "plain_text", "text": f"{status} [{agent.upper()}] Task Complete"}},
                {"type": "section",
                 "text": {"type": "mrkdwn", "text": f"*Task:* {task_desc[:120]}"}},
                {"type": "section",
                 "text": {"type": "mrkdwn", "text": f"```{preview}```"}},
                {"type": "divider"},
            ]
        )
    except SlackApiError as e:
        print(f"[Slack] {e.response['error']}")


def post_slack_alert(title: str, message: str, color: str = "good"):
    if not SLACK_BOT_TOKEN:
        return
    try:
        slack.chat_postMessage(
            channel=SLACK_CHANNEL,
            attachments=[{
                "color": color,
                "title": title,
                "text": message,
                "footer": "OpenClaw Swarm OS",
                "ts": int(__import__("time").time()),
            }]
        )
    except SlackApiError as e:
        print(f"[Slack Alert] {e.response['error']}")


# -- Bot setup --
intents = discord.Intents.default()
intents.message_content = True


class OpenClawBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("[OpenClaw] Slash commands synced to Discord")

    async def on_ready(self):
        init_db()
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the swarm | /swarm /deploy /status"
            )
        )
        print(f"[OpenClaw] MAIN BRAIN online as {self.user}")
        post_slack_alert("OpenClaw Online", f"MAIN BRAIN `{self.user}` is live and accepting commands.", "good")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if self.user in message.mentions:
            content = message.content.replace(f"<@{self.user.id}>", "").strip()
            if content:
                await message.channel.send(
                    f"MAIN BRAIN received: `{content[:100]}`\n"
                    f"Use `/create-task` to execute this with the swarm."
                )


client = OpenClawBot()
tree   = client.tree


# -- Agent runner --
async def run_agent(itx: discord.Interaction, agent: str, task_desc: str) -> str:
    tid = save_task(task_desc, agent)
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, lambda: process_task(task_desc, agent)
        )
        update_task(tid, result, "done")
        loop.run_in_executor(None, lambda: post_slack(agent, task_desc, result))
        preview = result[:900] + "..." if len(result) > 900 else result
        await itx.followup.send(
            f"[{agent.upper()}] -> Slack #{SLACK_CHANNEL}\n```{preview}```",
            ephemeral=False
        )
        return result
    except Exception as e:
        update_task(tid, str(e), "failed")
        post_slack(agent, task_desc, f"ERROR: {e}", "ERR")
        await itx.followup.send(f"[{agent}] failed: `{e}`")
        return ""


# -- /create-task --
@tree.command(name="create-task", description="MAIN BRAIN auto-plans and executes any task with the swarm")
@app_commands.describe(task="Describe what you want done (any complexity)")
async def create_task(itx: discord.Interaction, task: str):
    await itx.response.defer(thinking=True)
    try:
        plan_raw = await asyncio.get_event_loop().run_in_executor(
            None, lambda: orchestrate_task(task)
        )
        plan = json.loads(plan_raw)
    except Exception as e:
        plan = [{"agent": "orchestrator", "task": task}]
        await itx.followup.send(f"Planner error (`{e}`), running orchestrator direct.")

    valid_plan = [p for p in plan if p.get("agent") in AGENT_PERSONAS]
    agent_summary = " -> ".join(f"{p['agent']}" for p in valid_plan)
    embed = discord.Embed(
        title="OpenClaw Swarm Activated",
        description=f"**Task:** {task[:200]}",
        color=0x00ff88
    )
    embed.add_field(name="Execution Plan", value=agent_summary or "orchestrator", inline=False)
    embed.add_field(name="Agents Spawned", value=str(len(valid_plan)), inline=True)
    embed.add_field(name="Output", value=f"#{SLACK_CHANNEL}", inline=True)
    embed.set_footer(text="OpenClaw Swarm OS | Ultra God Mode")
    await itx.followup.send(embed=embed)

    post_slack_alert(
        "Swarm Task Started",
        f"Task: {task[:200]}\nPlan: {agent_summary}",
        "#439FE0"
    )
    await asyncio.gather(*[run_agent(itx, p["agent"], p["task"]) for p in valid_plan])
    save_decision(task, f"Plan: {agent_summary}", "executed")
    await itx.followup.send("All agents complete. Full output -> Slack.")


            f"Unknown agents: {', '.join(bad)}\n"
            f"Available: {', '.join(AGENT_PERSONAS.keys())}"
        )
        return
    await itx.followup.send(f"{len(agent_list)} agents on: *{task[:80]}*")
    await asyncio.gather(*[run_agent(itx, a, task) for a in agent_list])
    await itx.followup.send("Swarm done -> Slack")


# -- /deploy --
@tree.command(name="deploy", description="Deploy a service via Railway through the OPS agent")
@app_commands.describe(
    service="Service name to deploy",
    notes="Deployment notes or version tag"
)
async def deploy(itx: discord.Interaction, service: str, notes: str = ""):
    await itx.response.defer(thinking=True)
    task_desc = (
        f"Generate a complete Railway deployment plan for service: {service}. "
        f"Notes: {notes}. "
        f"Include: Dockerfile, railway.toml, env vars template, health check, rollback procedure."
    )
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: multi_agent_pipeline(task_desc, ["ops", "qa", "memory"])
    )
    ops_out = result.get("ops", "No OPS output")
    preview = ops_out[:800] + "..." if len(ops_out) > 800 else ops_out
    embed = discord.Embed(title=f"Deploy: {service}", color=0xff6600)
    embed.add_field(name="OPS Plan", value=f"```{preview}```", inline=False)
    embed.set_footer(text="QA + Memory agents also ran -> see Slack")
    await itx.followup.send(embed=embed)
    for agent, out in result.items():
        post_slack(agent, task_desc, out)
    await itx.followup.send("Deployment plan complete -> Slack")


# -- /github --
@tree.command(name="github", description="GitHub automation - PRs, issues, branches, Actions")
@app_commands.describe(action="What to do on GitHub (create PR, open issue, new branch, etc.)")
async def github_cmd(itx: discord.Interaction, action: str):
    await itx.response.defer(thinking=True)
    task_desc = (
        f"Execute this GitHub operation: {action}\n"
        f"Repository: {GITHUB_REPO or '<set GITHUB_REPO env var>'}\n"
        f"Return exact GitHub API payloads or gh CLI commands to run."
    )
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: process_task(task_desc, "github")
    )
    preview = result[:900] + "..." if len(result) > 900 else result
    await itx.followup.send(
        f"GITHUB AGENT output:\n```{preview}```"
    )
    post_slack("github", action, result)


# -- /status --
@tree.command(name="status", description="Swarm status - tasks, agents, deployments")
async def status_cmd(itx: discord.Interaction):
    s = get_stats()
    recent = get_recent_tasks(5)
    embed = discord.Embed(title="OpenClaw Swarm Status", color=0x0099ff)
    embed.add_field(name="Total Tasks", value=str(s.get("total_tasks", 0)), inline=True)
    embed.add_field(name="Running",     value=str(s.get("running", 0)),      inline=True)
    embed.add_field(name="Done",        value=str(s.get("done", 0)),          inline=True)
    embed.add_field(name="Failed",      value=str(s.get("failed", 0)),        inline=True)
    embed.add_field(name="Deployments", value=str(s.get("deployments", 0)),   inline=True)
    embed.add_field(name="Decisions",   value=str(s.get("decisions", 0)),     inline=True)
    if recent:
        task_lines = "\n".join(
            (f"`{t['id']}` **{t['agent']}** [{t['status']}] {t['desc'][:50]}"
            for t in recent)
        )
        embed.add_field(name="Recent Tasks", value=task_lines, inline=False)
    embed.set_footer(text="OpenClaw Swarm OS")
    await itx.response.send_message(embed=embed)


# -- /fix --
@tree.command(name="fix", description="Diagnose and fix a failing system or error")
@app_commands.describe(problem="Describe the error, failing service, or broken system")
async def fix_cmd(itx: discord.Interaction, problem: str):
    await itx.response.defer(thinking=True)
    task_desc = f"Diagnose and fix: {problem}. Provide step-by-step resolution + root cause analysis."
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: multi_agent_pipeline(task_desc, ["research", "coder", "qa"])
    )
    for agent, out in result.items():
        preview = out[:600] + "..." if len(out) > 600 else out
        await itx.followup.send(f"[{agent.upper()}]: ```{preview}```")
        post_slack(agent, problem, out)
    await itx.followup.send("Fix analysis complete -> Slack")


# -- /review --
@tree.command(name="review", description="Review code, architecture, or a PR")
@app_commands.describe(target="What to review (paste code, PR URL, or description)")
async def review_cmd(itx: discord.Interaction, target: str):
    await itx.response.defer(thinking=True)
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: process_task(target, "reviewer")
    )
    preview = result[:1200] + "..." if len(result) > 1200 else result
    await itx.followup.send(f"REVIEWER:\n```{preview}```")
    post_slack("reviewer", target[:80], result)


# -- /optimize --
@tree.command(name="optimize", description="Optimize performance, costs, or workflows")
@app_commands.describe(target="What to optimize (service, codebase, workflow, cost)")
async def optimize_cmd(itx: discord.Interaction, target: str):
    await itx.response.defer(thinking=True)
    task_desc = f"Optimize: {target}. Identify bottlenecks, reduce costs, improve speed and reliability."
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: multi_agent_pipeline(task_desc, ["research", "coder", "ops"])
    )
    for agent, out in result.items():
        preview = out[:500] + "..." if len(out) > 500 else out
        await itx.followup.send(f"[{agent.upper()}]: ```{preview}```")
        post_slack(agent, f"optimize: {target[:60]}", out)
    await itx.followup.send("Optimization plan complete -> Slack")


# -- /monitor --
@tree.command(name="monitor", description="Generate moni
        None, lambda: process_task(task_desc, "ops")
    )
    preview = result[:1000] + "..." if len(result) > 1000 else result
    await itx.followup.send(f"MONITORING PLAN for `{service}`:\n```{preview}```")
    post_slack("ops", f"monitor: {service}", result)


# -- /agents --
@tree.command(name="agents", description="List all OpenClaw swarm agents")
async def agents_cmd(itx: discord.Interaction):
    embed = discord.Embed(title="OpenClaw Swarm Agents", color=0x9b59b6)
    for name, persona in AGENT_PERSONAS.items():
        embed.add_field(name=f"{name.upper()}", value=persona[:120] + "...", inline=False)
    embed.set_footer(text="Use /swarm to manually select agents | /create-task for auto-planning")
    await itx.response.send_message(embed=embed)


# -- /rebuild --
@tree.command(name="rebuild", description="Rebuild a service or system from scratch")
@app_commands.describe(service="What to rebuild", requirements="Requirements or constraints")
async def rebuild_cmd(itx: discord.Interaction, service: str, requirements: str = ""):
    await itx.response.defer(thinking=True)
    task_desc = f"Rebuild {service} from scratch. Requirements: {requirements}. Full architecture + code + deployment."
    plan = [
        {"agent": "research",  "task": f"Research best architecture for {service}"},
        {"agent": "coder",     "task": task_desc},
        {"agent": "reviewer",  "task": f"Review the rebuilt {service} architecture and code"},
        {"agent": "qa",        "task": f"Write test plan for rebuilt {service}"},
        {"agent": "ops",       "task": f"Create deployment plan for rebuilt {service} on Railway"},
        {"agent": "memory",    "task": f"Log rebuild decision for {service}: {requirements}"},
    ]
    await itx.followup.send(f"Rebuilding `{service}` - 6 agents spawned")
    await asyncio.gather(*[run_agent(itx, p["agent"], p["task"]) for p in plan])
    await itx.followup.send("Rebuild complete -> Slack")


# -- /scale --
@tree.command(name="scale", description="Scale a service or infrastructure")
@app_commands.describe(service="Service to scale", direction="up or down", reason="Why scaling?")
async def scale_cmd(itx: discord.Interaction, service: str, direction: str = "up", reason: str = ""):
    await itx.response.defer(thinking=True)
    task_desc = (
        f"Scale {service} {direction}. Reason: {reason}. "
        f"Provide: Railway scaling config, resource adjustments, cost impact, rollback plan."
    )
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: process_task(task_desc, "ops")
    )
    preview = result[:900] + "..." if len(result) > 900 else result
    await itx.followup.send(f"SCALE {direction.upper()} `{service}`:\n```{preview}```")
    post_slack("ops", f"scale {direction}: {service}", result)


# -- /stop --
@tree.command(name="stop", description="Emergency stop - halt all running operations")
async def stop_cmd(itx: discord.Interaction):
    embed = discord.Embed(
        title="EMERGENCY STOP ACKNOWLEDGED",
        description=(
            "MAIN BRAIN received stop signal.\n\n"
            "To fully halt Railway services:\n"
            "```railway down --service <name>```\n"
            "To cancel GitHub Actions:\n"
            "```gh run cancel <run-id>```\n"
            "Slack alert sent to ops channel."
        ),
        color=0xff0000
    )
    await itx.response.send_message(embed=embed)
    post_slack_alert("EMERGENCY STOP", f"Stop issued by {itx.user}", "danger")


# -- /resume --
@tree.command(name="resume", description="Resume operations after a stop")
async def resume_cmd(itx: discord.Interaction):
    await itx.response.send_message(
        "Resuming operations. MAIN BRAIN is active. Use /create-task or /swarm to continue."
    )
    post_slack_alert("Operations Resumed", f"Resumed by {itx.user}", "good")


# -- run --
client.run(DISCORD_TOKEN)
toring plan for a service")
@app_commands.describe(service="Service or system to monitor")
async def monitor_cmd(itx: discord.Interaction, service: str):
    await itx.response.defer(thinking=True)
    task_desc = (
        f"Create a comprehensive monitoring plan for: {service}. "
        f"Include: health checks, alerting thresholds, Slack alert configs, "
        f"uptime monitoring, error rate tracking, Railway metrics."
    )
    result = await asyncio.get_event_loop().run_in_executor(

# -- /swarm --
@tree.command(name="swarm", description="Manually assign agents to a task")
@app_commands.describe(
    agents="Comma-separated: coder,reviewer,qa,ops,research,growth,memory,github",
    task="What to execute"
)
async def swarm(itx: discord.Interaction, agents: str, task: str):
    await itx.response.defer(thinking=True)
    agent_list = [a.strip() for a in agents.split(",")]
    bad = [a for a in agent_list if a not in AGENT_PERSONAS]
    if bad:
        await itx.followup.send(
