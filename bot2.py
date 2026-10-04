import os
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

if not DISCORD_TOKEN or not OPENAI_KEY:
    raise ValueError("❌.env belum diatur!")

openai_client = OpenAI(api_key=OPENAI_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Database dummy - di real world jangan simpen password mentah!
MOCK_LEAK_DATABASE = [
    {"email": "budi@gmail.com", "source": "Adobe 2013 Leak"},
    {"email": "budi@gmail.com", "source": "Linkedin 2016 Leak"},
    {"email": "siti@yahoo.com", "source": "Canva 2019 Leak"}
]

def search_leak_db_safe(query: str) -> list:
    results = [e for e in MOCK_LEAK_DATABASE if query.lower() in e['email'].lower()]
    print(f"[AMAN] Cek {query} -> {len(results)} sumber")
    return results

def analyze_with_llm_safe(leak_data: list, email: str) -> str:
    sources = [d['source'] for d in leak_data]
    prompt = (
        f"Email '{email}' ditemukan di {len(sources)} sumber kebocoran: {sources}. "
        f"Berikan edukasi risiko dan langkah mitigasi (ganti password, 2FA, cek haveibeenpwned) "
        f"JANGAN PERNAH sebutkan, tebak, atau tampilkan password."
    )
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Kamu adalah ahli keamanan siber. Jangan pernah menampilkan password."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

@bot.event
async def on_ready():
    print(f'🤖 Bot online sebagai {bot.user.name}')

@bot.command(name='check')
async def check_email(ctx, email: str):
    try:
        await ctx.message.delete()
    except:
        pass

    status_msg = await ctx.send(f"🔒 {ctx.author.mention}, cek privasi dimulai. Hasil via DM ya!")

    raw_results = search_leak_db_safe(email)
    if not raw_results:
        try:
            await ctx.author.send(f"✅ Aman! Tidak ada data bocor untuk `{email}`")
            await status_msg.edit(content=f"✅ {ctx.author.mention}, hasil sudah di DM.")
        except:
            await status_msg.edit(content=f"❌ {ctx.author.mention}, buka DM dulu ya.")
        return

    try:
        ai_analysis = analyze_with_llm_safe(raw_results, email)
        await ctx.author.send(f"⚠️ **LAPORAN RAHASIA**\nEmail: `{email}`\nDitemukan di {len(raw_results)} sumber\n\n{ai_analysis}")
        await status_msg.edit(content=f"⚠️ {ctx.author.mention}, laporan lengkap udah di DM!")
    except Exception as e:
        print(f"[ERROR] {e}")
        await status_msg.edit(content=f"❌ Error internal.")

bot.run(DISCORD_TOKEN)