import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 서버 설정을 저장하는 딕셔너리
server_settings = {}

# JSON 파일에서 설정 불러오기
def load_settings():
    global server_settings
    try:
        with open('server_settings.json', 'r') as f:
            server_settings = json.load(f)
    except FileNotFoundError:
        # 파일이 없을 경우 기본 설정 생성
        server_settings = {}

# 설정을 JSON 파일에 저장
def save_settings():
    with open('server_settings.json', 'w') as f:
        json.dump(server_settings, f, indent=4)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} is ready!')
    load_settings()  # 봇이 온라인 상태일 때 설정 불러오기

@bot.command()
async def setlogchannel(ctx, channel: discord.TextChannel):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_settings:
        server_settings[guild_id] = {'log_channel': None}  # 각 서버의 기본 설정

    server_settings[guild_id]['log_channel'] = channel.id
    save_settings()
    await ctx.send(f"로그 채널이 {channel.mention}으로 설정되었습니다.")

@bot.event
async def on_member_join(member):
    guild = member.guild
    join_date = member.created_at
    current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
    difference = current_time - join_date
    thirty_days = timedelta(days=30)
    
    guild_id = str(guild.id)
    if guild_id not in server_settings:
        server_settings[guild_id] = {'log_channel': None}  # 각 서버의 기본 설정
    
    if difference < thirty_days:
        await member.ban(reason="계정 생성 후 30일이 지나지 않았습니다.")
        print(f"{member}는 계정 생성 후 30일이 지나지 않아 차단되었습니다.")
        log_channel_id = server_settings[guild_id]['log_channel']
        if log_channel_id:
            log_channel = bot.get_channel(log_channel_id)
            await log_channel.send(f"{member}는 계정 생성 후 30일이 지나지 않아 차단되었습니다.")

bot.run('MTE5MDYzMjA2ODE2MjUzMTMyOA.Ghux2l.1eZcwSgauFkeBZHSLBz0zI2mFgsGxQDaLFmvfs')
