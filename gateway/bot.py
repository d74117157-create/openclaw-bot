"""
OpenClaw - gateway/bot.py
Extended Discord bot with task management and deployment slash commands.
"""
import os, asyncio, traceback, json
import discord
from discord import app_commands
from dotenv import load_dotenv
from memory import init_db, save_task, update_task, get_stats, save_decision
from worker.ai_worker import process_task, orchestrate_task, AGENT_PERSONAS
from worker.github_agent import push_file, list_repo_files

load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
BRAIN_CHANNEL = os.environ.get("BRAIN_CHANNEL", "brain")

intents = discord.Intents.default()
intents.message_content = True


class OpenClawBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        init_db()

    async def on_ready(self):
        print(f"[OpenClawBot] Online as {self.user}")


bot  = OpenClawBot()
tree = bot.tree


# -- Helpers ------------------------------------------------------------------

def _embed(title: str, desc: str, color: int = 0x00bfff) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=color)
    e.set_footer(text="OpenClaw")
    return e


async def _run_agent(agent: str, task_desc: str) -> str:
    loop = asyncio.get_event_loop()
    tid  = save_task(task_desc, agent)
    try:
        result = await loop.run_in_executor(None, process_task, task_desc, agent)
        update_task(tid, result, "done")
        return result
    except Exception as exc:
        update_task(tid, str(exc), "failed")
        raise


# -- Slash Commands -----------------------------------------------------------

@tree.command(name="create-task", description="Create and assign a task to an agent")
@app_commands.describe(agent="Agent name (coder, reviewer, qa, ops, research, growth)",
                       task="Task description")
async def cmd_create_task(interaction: discord.Interaction, agent: str, task: str):
    await interaction.response.defer()
    try:
        result = await _run_agent(agent, task)
        await interaction.followup.send(
            embed=_embed(f"[{agent}] Task Complete", result[:3900])
        )
    except Exception:
        await interaction.followup.send(
            embed=_embed("Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


@tree.command(name="swarm", description="Run full swarm on a task")
@app_commands.describe(task="Task for the swarm")
async def cmd_swarm(interaction: discord.Interaction, task: str):
    await interaction.response.defer()
    try:
        loop    = asyncio.get_event_loop()
        raw     = await loop.run_in_executor(None, orchestrate_task, task)
        plan    = json.loads(raw)
        results = []
        for step in plan:
            agent = step.get("agent", "orchestrator")
            sub   = step.get("task", task)
            out   = await _run_agent(agent, sub)
            results.append(f"**[{agent}]**: {out[:300]}")
        combined = "\n\n".join(results) or "No output."
        await interaction.followup.send(
            embed=_embed("[swarm] Done", combined[:3900], color=0x00ff88)
        )
    except Exception:
        await interaction.followup.send(
            embed=_embed("[swarm] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


@tree.command(name="deploy", description="Trigger a deployment via ops agent")
@app_commands.describe(target="What to deploy")
async def cmd_deploy(interaction: discord.Interaction, target: str = "main"):
    await interaction.response.defer()
    try:
        result = await _run_agent("ops", f"Deploy {target} to production")
        await interaction.followup.send(
            embed=_embed("[deploy] Result", result[:3900], color=0xffaa00)
        )
    except Exception:
        await interaction.followup.send(
            embed=_embed("[deploy] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


@tree.command(name="github", description="GitHub agent actions")
@app_commands.describe(action="list or push", path="File path", content="Content for push")
async def cmd_github(interaction: discord.Interaction,
                     action: str,
                     path: str = "",
                     content: str = ""):
    await interaction.response.defer()
    try:
        if action == "list":
            files = list_repo_files()
            await interaction.followup.send(
                embed=_embed("[github] Files", "\n".join(files[:50])[:3900])
            )
        elif action == "push" and path and content:
            push_file(path, content, f"Update {path} via Discord")
            await interaction.followup.send(
                embed=_embed("[github] Pushed", f"`{path}` updated.")
            )
        else:
            await interaction.followup.send(
                embed=_embed("[github] Usage", "`/github action:list` or `/github action:push path:... content:...`")
            )
    except Exception:
        await interaction.followup.send(
            embed=_embed("[github] Error", f"```{traceback.format_exc()[-800:]}```", color=0xff4444)
        )


@tree.command(name="agents", description="List available agents")
async def cmd_agents(interaction: discord.Interaction):
    lines = [f"**{k}** — {v[:90]}..." for k, v in AGENT_PERSONAS.items()]
    await interaction.response.send_message(
        embed=_embed("Available Agents", "\n".join(lines))
    )


@tree.command(name="status", description="Show bot status and recent tasks")
async def cmd_status(interaction: discord.Interaction):
    stats = get_stats()
    embed = _embed("OpenClaw Status",
                   f"Tasks: **{stats['total']}** | Done: **{stats['done']}** | Failed: **{stats['failed']}**")
    await interaction.response.send_message(embed=embed)




# -- Trading Agent Commands ---------------------------------------------------

from worker.agents.trader import get_trader
from worker.agents.risk_manager import RiskManager

risk_mgr = RiskManager()

@tree.command(name="trade", description="Execute a trade via swarm")
@app_commands.describe(
    exchange="binance (more coming)",
    symbol="e.g. BTC/USDT",
    side="buy or sell",
    qty="Amount to trade"
)
async def cmd_trade(interaction: discord.Interaction, exchange: str, symbol: str, side: str, qty: float):
    await interaction.response.defer()
    try:
        trader = get_trader(exchange)
        price = trader.get_price(symbol)
        risk = risk_mgr.check_trade(trader, symbol, side, qty, price)
        if not risk["approved"]:
            await interaction.followup.send(f"🚫 **RISK BLOCKED:** {risk['reason']}")
            return
        result = trader.place_order(symbol, side, qty)
        embed = discord.Embed(title=f"📈 Trade Executed", color=0x00ff00 if side == "buy" else 0xff0000)
        embed.add_field(name="Exchange", value=exchange.upper(), inline=True)
        embed.add_field(name="Symbol", value=symbol.upper(), inline=True)
        embed.add_field(name="Side", value=side.upper(), inline=True)
        embed.add_field(name="Qty", value=str(qty), inline=True)
        embed.add_field(name="Price", value=f"${price:,.2f}", inline=True)
        embed.add_field(name="Notional", value=f"${qty * price:,.2f}", inline=True)
        embed.add_field(name="Mode", value="PAPER" if trader.paper else "LIVE", inline=True)
        embed.add_field(name="Status", value=result.get("status", "unknown"), inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Trade failed: {str(e)}")

@tree.command(name="balance", description="Check trading balance")
@app_commands.describe(exchange="binance")
async def cmd_balance(interaction: discord.Interaction, exchange: str):
    await interaction.response.defer()
    try:
        trader = get_trader(exchange)
        bal = trader.get_balance()
        embed = discord.Embed(title=f"💰 {exchange.upper()} Balance", color=0x3498db)
        embed.add_field(name="Asset", value=bal.get("asset", "USDT"), inline=True)
        embed.add_field(name="Total", value=f"${bal.get('total', 0):,.2f}", inline=True)
        embed.add_field(name="Free", value=f"${bal.get('free', 0):,.2f}", inline=True)
        embed.add_field(name="Mode", value="PAPER" if trader.paper else "LIVE", inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@tree.command(name="positions", description="View active positions")
@app_commands.describe(exchange="binance")
async def cmd_positions(interaction: discord.Interaction, exchange: str):
    await interaction.response.defer()
    try:
        trader = get_trader(exchange)
        pos = trader.get_positions()
        if not pos:
            await interaction.followup.send("📭 No active positions.")
            return
        embed = discord.Embed(title=f"📊 {exchange.upper()} Positions", color=0x9b59b6)
        for i, p in enumerate(pos[-5:], 1):
            embed.add_field(
                name=f"#{i} {p['symbol']}",
                value=f"{p['side'].upper()} {p['qty']} @ ${p['price']:,.2f} | Notional: ${p['notional']:,.2f}",
                inline=False
            )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")




@tree.command(name="portfolio", description="View swarm portfolio history and stats")
@app_commands.describe(asset="Filter by asset (e.g. USDT, BTC)")
async def cmd_portfolio(interaction: discord.Interaction, asset: str = None):
    await interaction.response.defer()
    try:
        from memory.core import get_memory
        mem = get_memory()

        # Get summary
        summary = mem.get_swarm_summary()

        # Get portfolio history
        history = mem.get_portfolio_history(asset, limit=10)

        embed = discord.Embed(title="📊 Swarm Portfolio", color=0x00ff00)
        embed.add_field(name="Total Trades", value=str(summary.get("total_trades", 0)), inline=True)
        embed.add_field(name="Total P&L", value=f"${summary.get('total_pnl', 0):,.2f}", inline=True)
        embed.add_field(name="Decisions Logged", value=str(summary.get("total_decisions", 0)), inline=True)

        if history:
            latest = history[0]
            embed.add_field(name="Latest Balance", value=f"${latest.get('value_usd', 0):,.2f} {latest.get('asset', 'USDT')}", inline=True)
            embed.add_field(name="Last Update", value=latest.get('timestamp', 'N/A')[:16], inline=True)

        embed.add_field(name="DB Path", value=summary.get("db_path", "N/A"), inline=False)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# -- Run ----------------------------------------------------------------------

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
