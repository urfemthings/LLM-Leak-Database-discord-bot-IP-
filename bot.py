import os
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

# 1. Muat variabel lingkungan
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

# Validasi kredensial dasar
if not DISCORD_TOKEN or not OPENAI_KEY:
    raise ValueError("❌ Variabel lingkungan DISCORD_TOKEN atau OPENAI_API_KEY belum diatur di file .env!")

# 2. Inisialisasi Klien OpenAI & Bot Discord
openai_client = OpenAI(api_key=OPENAI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 3. Simulasi Database Kebocoran Data (Ganti dengan DB sungguhan jika produksi)
MOCK_LEAK_DATABASE = [
    {"email": "budi@gmail.com", "password": "password123", "source": "Adobe 2013 Leak"},
    {"email": "budi@gmail.com", "password": "budi_ganteng", "source": "Linkedin 2016 Leak"},
    {"email": "siti@yahoo.com", "password": "qwertyasdf", "source": "Canva 2019 Leak"}
]

def search_leak_db(query: str) -> list:
    """Mencari data email di dalam database kebocoran & print log password mentah."""
    results = [entry for entry in MOCK_LEAK_DATABASE if query.strip().lower() in entry['email'].lower()]
    
    # === LOG / PRINT EMAIL DAN PASSWORD MENTAH DARI DATABASE ===
    print(f"\n[DATABASE LOG] Pencarian untuk email: {query} | Ditemukan: {len(results)} entri.")
    for entry in results:
        print(f" -> [DB DATA] Email: {entry['email']} | Password Mentah: {entry['password']} | Sumber: {entry['source']}")
        
    return results

def analyze_with_llm(leak_data: list, email: str) -> str:
    """Meminta LLM menganalisis data mentah asli (termasuk password mentah)."""
    
    # === LOG / PRINT DATA MENTAH YANG DIKIRIM KE LLM ===
    print(f"\n[LLM LOG MENTAH] Mengirim data ke OpenAI untuk email: {email}")
    for entry in leak_data:
        print(f" -> [LLM PAYLOAD] Email: {email} | Password Mentah: {entry.get('password')} | Sumber: {entry.get('source')}")
    
    # Mengirimkan data mentah asli ke prompt LLM
    prompt = (
        f"Berikut adalah data mentah kebocoran asli yang ditemukan untuk email '{email}':\n"
        f"{str(leak_data)}\n\n"
        f"Berikan analisis risiko keamanan siber yang mendalam dan rekomendasi tindakan mitigasi "
        f"yang harus segera dilakukan oleh pengguna berdasarkan data tersebut."
    )
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "Anda adalah seorang ahli ketahanan siber profesional yang memberikan saran keamanan data yang objektif dan jelas."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

@bot.event
async def on_ready():
    print(f'🤖 Bot telah online dan masuk sebagai {bot.user.name}')

@bot.command(name='check')
async def check_email(ctx, email: str):
    """Perintah untuk mengecek kebocoran data berdasarkan email secara aman via DM."""
    # Hapus pesan perintah asli di publik demi privasi agar email tidak terpampang lama
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass # Lewati jika bot tidak punya izin 'Manage Messages'

    # Kirim status awal singkat menggunakan ctx.send() di channel publik
    status_msg = await ctx.send(f"🔒 {ctx.author.mention}, pemeriksaan privasi dimulai. Hasil laporan akan dikirim melalui **Direct Message (DM)** demi keamanan data Anda.")
    
    # 1. Jalankan Query Database & Log Print
    raw_results = search_leak_db(email)
    
    if not raw_results:
        try:
            await ctx.author.send(f"✅ **Aman!** Tidak ditemukan adanya data bocor untuk email `{email}` di database kami.")
            await status_msg.edit(content=f"✅ {ctx.author.mention}, hasil pemeriksaan telah dikirim ke DM Anda.")
        except discord.Forbidden:
            await status_msg.edit(content=f"❌ {ctx.author.mention}, Gagal mengirim DM. Mohon buka pengaturan privasi DM server Anda.")
        return
    
    # 2. Analisis menggunakan AI (dengan data mentah) & Kirim via DM
    try:
        ai_analysis = analyze_with_llm(raw_results, email)
        
        response_message = (
            f"⚠️ **LAPORAN KEBOCORAN DATA (RAHASIA)** ⚠️\n"
            f"Target Email: `{email}`\n"
            f"**Total Sumber Bocor Ditemukan:** {len(raw_results)}\n\n"
            f"**Analisis & Rekomendasi Pakar:**\n{ai_analysis}"
        )
        
        # Kirim laporan lengkap langsung ke DM pengguna
        await ctx.author.send(response_message)
        await status_msg.edit(content=f"⚠️ {ctx.author.mention}, ditemukan indikasi kebocoran! Laporan lengkap telah dikirim ke **Direct Message (DM)** Anda.")
        
    except discord.Forbidden:
        await status_msg.edit(content=f"❌ {ctx.author.mention}, Data ditemukan, tetapi bot tidak dapat mengirim DM ke akun Anda. Pastikan DM diaktifkan.")
    except Exception as e:
        print(f"[ERROR LOG] {str(e)}")
        await status_msg.edit(content=f"❌ Terjadi kesalahan internal saat memproses analisis AI.")

# Jalankan Bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)