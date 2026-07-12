"""
KingLulu Digital Product Catalog
30 products ready to sell across Gumroad, Payhip, Etsy.
"""

KINGLULU_PRODUCTS = [
    # eBooks ($7) — Lead magnets
    {"type": "ebook", "title": "The AI Automation Playbook", "topic": "ai automation", "price": 7.00},
    {"type": "ebook", "title": "7 AI Tools That Print Money", "topic": "ai tools", "price": 7.00},
    {"type": "ebook", "title": "Zero to $1K: AI Side Hustle Guide", "topic": "side hustle", "price": 7.00},
    {"type": "ebook", "title": "The Lazy Person's Guide to Wealth", "topic": "passive income", "price": 7.00},
    {"type": "ebook", "title": "Crypto Trading for Beginners", "topic": "crypto trading", "price": 7.00},
    {"type": "ebook", "title": "How to Build a Bot Army", "topic": "bot building", "price": 7.00},
    {"type": "ebook", "title": "The $0 Startup Blueprint", "topic": "startup", "price": 7.00},
    {"type": "ebook", "title": "AI Content Machine: YouTube + TikTok", "topic": "content creation", "price": 7.00},
    {"type": "ebook", "title": "The Truth About Passive Income", "topic": "passive income", "price": 7.00},
    {"type": "ebook", "title": "Automated Sales Funnels That Convert", "topic": "sales funnels", "price": 7.00},

    # Guides ($27) — Core products
    {"type": "guide", "title": "The Complete AI Empire Blueprint", "topic": "ai empire", "price": 27.00},
    {"type": "guide", "title": "Trading Bot Mastery: Build & Deploy", "topic": "trading bots", "price": 27.00},
    {"type": "guide", "title": "The Digital Product Factory", "topic": "digital products", "price": 27.00},
    {"type": "guide", "title": "YouTube Automation: 0 to 100K Subs", "topic": "youtube growth", "price": 27.00},
    {"type": "guide", "title": "TikTok Viral Formula: 1M Views", "topic": "tiktok viral", "price": 27.00},
    {"type": "guide", "title": "The Affiliate Marketing Bible", "topic": "affiliate marketing", "price": 27.00},
    {"type": "guide", "title": "Email Sequences That Print Money", "topic": "email marketing", "price": 27.00},
    {"type": "guide", "title": "SEO Domination: Rank #1 on Google", "topic": "seo", "price": 27.00},
    {"type": "guide", "title": "The Freelancer to Founder Transition", "topic": "freelancing", "price": 27.00},
    {"type": "guide", "title": "AI-Powered E-commerce: No Inventory", "topic": "ecommerce", "price": 27.00},

    # Templates ($17) — Quick wins
    {"type": "template", "title": "AI Prompt Library: 500+ Prompts", "topic": "ai prompts", "price": 17.00},
    {"type": "template", "title": "YouTube Script Templates Pack", "topic": "youtube scripts", "price": 17.00},
    {"type": "template", "title": "TikTok Hook Swipe File", "topic": "tiktok hooks", "price": 17.00},
    {"type": "template", "title": "Email Funnel Templates: 20 Sequences", "topic": "email templates", "price": 17.00},
    {"type": "template", "title": "Notion Dashboard: Business OS", "topic": "notion templates", "price": 17.00},

    # Courses ($97) — High ticket
    {"type": "course", "title": "AI Empire Builder: Full Course", "topic": "ai empire", "price": 97.00},
    {"type": "course", "title": "Trading Bot Accelerator", "topic": "trading bots", "price": 97.00},
    {"type": "course", "title": "Content Machine Masterclass", "topic": "content creation", "price": 97.00},
    {"type": "course", "title": "The Passive Income Machine", "topic": "passive income", "price": 97.00},
    {"type": "course", "title": "Digital Empire: From Zero to $10K/Month", "topic": "digital empire", "price": 97.00},
]

def get_all_products():
    return KINGLULU_PRODUCTS

def get_products_by_type(product_type: str):
    return [p for p in KINGLULU_PRODUCTS if p["type"] == product_type]

def get_products_by_platform(platform: str):
    platform_map = {
        "gumroad": ["ebook", "guide", "course", "template", "bundle"],
        "payhip": ["ebook", "guide", "course", "template", "bundle", "membership"],
        "etsy": ["template", "ebook", "guide"],
        "shopify": ["guide", "course", "bundle"],
        "teachable": ["course"],
        "patreon": ["membership"]
    }
    types = platform_map.get(platform, ["ebook"])
    return [p for p in KINGLULU_PRODUCTS if p["type"] in types]
