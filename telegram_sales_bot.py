"""
KingLulu Telegram Bot — Sales + Product Drops
Auto-sells digital products. Broadcasts new launches.
"""
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TELEGRAM_BOT1_TOKEN = os.getenv("TELEGRAM_BOT1_TOKEN", "")
TELEGRAM_BOT2_TOKEN = os.getenv("TELEGRAM_BOT2_TOKEN", "")
TELEGRAM_BOT3_TOKEN = os.getenv("TELEGRAM_BOT3_TOKEN", "")

PAYHIP_STORE = "https://payhip.com/b/lAr1N"
GUMROAD_STORE = "https://gumroad.com/kinglulu"

class KingLuluTelegramBot:
    def __init__(self, token, name="KingLulu"):
        self.token = token
        self.name = name
        self.app = Application.builder().token(token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("products", self.cmd_products))
        self.app.add_handler(CommandHandler("buy", self.cmd_buy))
        self.app.add_handler(CommandHandler("free", self.cmd_free))
        self.app.add_handler(CommandHandler("bundle", self.cmd_bundle))
        self.app.add_handler(CommandHandler("support", self.cmd_support))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome = f"""🦅 Welcome to {self.name}'s Empire

I build AI-powered income streams.

📦 COMMANDS:
/products — See all digital products
/buy — Quick buy menu
/free — Free resources
/bundle — Best value deals
/support — Get help

💰 Every product comes with:
✅ Instant delivery
✅ 30-day guarantee
✅ Free updates

🔥 Start with the FREE guide:"""

        keyboard = [
            [InlineKeyboardButton("🎁 FREE Guide", url=PAYHIP_STORE)],
            [InlineKeyboardButton("📦 All Products", callback_data="products")],
            [InlineKeyboardButton("💎 Best Bundle", callback_data="bundle")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome, reply_markup=reply_markup)

    async def cmd_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        products_text = """📦 KINGLULU DIGITAL PRODUCTS

💎 eBooks ($7):
• The AI Automation Playbook
• 7 AI Tools That Print Money
• Zero to $1K: AI Side Hustle
• Crypto Trading for Beginners
• How to Build a Bot Army

📘 Guides ($27):
• The Complete AI Empire Blueprint
• Trading Bot Mastery
• YouTube Automation: 0 to 100K
• TikTok Viral Formula
• The Affiliate Marketing Bible

🎓 Courses ($97):
• AI Empire Builder: Full Course
• Trading Bot Accelerator
• Content Machine Masterclass

🛠️ Templates ($17):
• AI Prompt Library (500+)
• YouTube Script Templates
• TikTok Hook Swipe File
• Email Funnel Templates

📚 BUNDLES ($197):
• The Ultimate AI Empire Bundle
• Everything Pack (All Products)
"""
        keyboard = [
            [InlineKeyboardButton("🛒 Buy on Payhip", url=PAYHIP_STORE)],
            [InlineKeyboardButton("🛒 Buy on Gumroad", url=GUMROAD_STORE)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(products_text, reply_markup=reply_markup)

    async def cmd_buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("💎 eBook ($7)", url=f"{PAYHIP_STORE}")],
            [InlineKeyboardButton("📘 Guide ($27)", url=f"{PAYHIP_STORE}")],
            [InlineKeyboardButton("🎓 Course ($97)", url=f"{PAYHIP_STORE}")],
            [InlineKeyboardButton("🛠️ Template ($17)", url=f"{PAYHIP_STORE}")],
            [InlineKeyboardButton("📚 Bundle ($197)", url=f"{PAYHIP_STORE}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("💰 What do you want to build?", reply_markup=reply_markup)

    async def cmd_free(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        free_text = """🎁 FREE RESOURCES

Start your empire with zero cost:

✅ The AI Automation Starter Guide
✅ 100 Profitable AI Business Ideas
✅ Trading Bot Setup Checklist
✅ YouTube Growth Hacks PDF
✅ TikTok Viral Hooks Swipe File

All free. No email required.
Just grab and build."""

        keyboard = [
            [InlineKeyboardButton("🎁 Get FREE Guide", url=PAYHIP_STORE)],
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/kinglulu_empire")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(free_text, reply_markup=reply_markup)

    async def cmd_bundle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bundle_text = """📚 THE ULTIMATE BUNDLE — $197

Everything I sell. One price. Lifetime access.

Includes:
✅ All 10 eBooks ($70 value)
✅ All 10 Guides ($270 value)
✅ All 5 Courses ($485 value)
✅ All 5 Template Packs ($85 value)
✅ Future products FREE
✅ Private Discord access
✅ Monthly Q&A calls

💰 Total Value: $910
🔥 Bundle Price: $197
💵 You Save: $713

⚡ Limited to 100 buyers."""

        keyboard = [
            [InlineKeyboardButton("🔥 GET THE BUNDLE", url=PAYHIP_STORE)],
            [InlineKeyboardButton("💬 Questions? DM @kinglulu", url="https://t.me/kinglulu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(bundle_text, reply_markup=reply_markup)

    async def cmd_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🛠️ SUPPORT\n\n"
            "Questions? Issues?\n"
            "Email: Luluharvey778@gmail.com\n"
            "Discord: OpenClaw Empire\n"
            "Response time: Under 24 hours\n\n"
            "For urgent issues, DM @kinglulu"
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "products":
            await self.cmd_products(update, context)
        elif query.data == "bundle":
            await self.cmd_bundle(update, context)

    async def broadcast_new_product(self, product: dict, channel_id: str = None):
        """Broadcast new product to channel."""
        if not channel_id:
            return

        message = f"""🚀 NEW PRODUCT DROP

📦 {product['title']}
💰 ${product['price']}
🏷️ {product['type'].upper()}

{product.get('description', 'Grab it now.')}

👇 Link in bio"""

        await self.app.bot.send_message(chat_id=channel_id, text=message)

    def run(self):
        print(f"[TELEGRAM] 🤖 {self.name} bot starting...")
        self.app.run_polling()

def start_telegram_bots():
    """Start all 3 Telegram bots."""
    bots = []

    if TELEGRAM_BOT1_TOKEN:
        bot1 = KingLuluTelegramBot(TELEGRAM_BOT1_TOKEN, "KingLulu Bot 1")
        bots.append(bot1)

    if TELEGRAM_BOT2_TOKEN:
        bot2 = KingLuluTelegramBot(TELEGRAM_BOT2_TOKEN, "KingLulu Bot 2")
        bots.append(bot2)

    if TELEGRAM_BOT3_TOKEN:
        bot3 = KingLuluTelegramBot(TELEGRAM_BOT3_TOKEN, "KingLulu Super")
        bots.append(bot3)

    print(f"[TELEGRAM] ✅ {len(bots)} bots ready")
    return bots

if __name__ == "__main__":
    bots = start_telegram_bots()
    if bots:
        bots[0].run()
