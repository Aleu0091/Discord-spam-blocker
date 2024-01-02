import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} is ready!')

@bot.event
async def on_member_join(member):
    join_date = member.created_at
    current_time = datetime.utcnow().replace(tzinfo=timezone.utc) 
    difference = current_time - join_date
    thirty_days = timedelta(days=30)
    if difference < thirty_days:
        await member.ban(reason="계정 생성 후 30일이 지나지 않았습니다.")
        print(f"{member}는 계정 생성 후 30일이 지나지 않아 차단되었습니다.")

@bot.event
async def on_member_remove(member):
    join_date = member.created_at
    current_time = datetime.utcnow().replace(tzinfo=timezone.utc)  
    difference = current_time - join_date
    thirty_days = timedelta(days=30)
    if difference < thirty_days:
        await member.ban(reason="계정 생성 후 30일이 지나지 않았습니다.")
        print(f"{member}는 오프라인 상태에서 계정 생성 후 30일이 지나지 않아 차단되었습니다.")

bot.run('')
