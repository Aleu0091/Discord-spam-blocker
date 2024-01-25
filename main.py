import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import sqlite3,pytz,time,key,os,asyncio
from discord import Option
import random
from PIL import Image, ImageDraw, ImageFont
import io
import string
# 새로운 봇 인스턴스 생성
bot = commands.Bot(command_prefix='!')


intents = discord.Intents.default()
intents.guilds = True
intents.members = True
start_time = time.time()
bot = commands.Bot(command_prefix='!', intents=intents)
current_datetime = datetime.now()
# 날짜 및 시간을 문자열로 변환하여 초까지 포맷팅
formatted_datetime = current_datetime.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")
# SQLite 데이터베이스 연결
conn = sqlite3.connect('bot.db')
c = conn.cursor()
Developers = key.DEVELOPERS_ID
c.execute('''CREATE TABLE IF NOT EXISTS log_channels
             (guild_id INTEGER PRIMARY KEY, log_channel INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS autoban_settings
             (guild_id INTEGER PRIMARY KEY, autoban_enabled INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS autoban_thresholds
             (guild_id INTEGER PRIMARY KEY, autoban_threshold INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS entry_exit_log_settings
             (guild_id INTEGER PRIMARY KEY, entry_exit_log_enabled INTEGER)''')

# 경고 테이블 생성 (기존 테이블이 이미 존재할 수 있음)
c.execute('''CREATE TABLE IF NOT EXISTS warnings
             (guild_id INTEGER, user_id INTEGER, warnings INTEGER, reason TEXT, timestamp TEXT, PRIMARY KEY (guild_id, user_id))''')

c.execute('''CREATE TABLE IF NOT EXISTS spam_prevention_settings
             (guild_id INTEGER PRIMARY KEY, anti_spam_enabled INTEGER)''')
c.execute('''
CREATE TABLE IF NOT EXISTS server_settings (
    server_id INTEGER PRIMARY KEY,
    captcha_enabled INTEGER,
    success_role_id INTEGER
)
''')
conn.commit()
def is_bot_owner(ctx):
    return ctx.author.id in Developers
def count_lines(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        return len(lines)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} is ready!')
    for filename in os.listdir("Cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"Cogs.{filename[:-3]}")


@bot.slash_command(name= "자동차단",description="유저 생성일이 지정된 생성일자보다 적을시 자동으로 차단합니다.")
async def toggle_autoban(ctx, situation : Option(description='상태를 설정해주세요', choices=['활성화', '비활성화'],required=True)):
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return


    c.execute('SELECT log_channel FROM log_channels WHERE guild_id=?', (ctx.guild.id,))
    result = c.fetchone()
    if result:
        log_channel_id = result[0]

        c.execute('SELECT autoban_enabled FROM autoban_settings WHERE guild_id=?', (ctx.guild.id,))
        autoban_result = c.fetchone()
        if autoban_result:
            autoban_enabled = bool(autoban_result[0])

            if autoban_enabled:
                # 비활성화
                if situation == "활성화":
                    await ctx.respond(embed=discord.Embed(title='자동 차단 활성화', description='자동 차단 기능이 이미 활성화되어있습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
                elif situation == "비활성화":
                    c.execute('UPDATE autoban_settings SET autoban_enabled=? WHERE guild_id=?', (0, ctx.guild.id))
                    conn.commit()
                    await ctx.respond(embed=discord.Embed(title='자동 차단 비활성화', description='자동 차단 기능이 비활성화되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
            else:
                if situation == "활성화":
                    c.execute('UPDATE autoban_settings SET autoban_enabled=? WHERE guild_id=?', (1, ctx.guild.id))
                    conn.commit()  
                    await ctx.respond(embed=discord.Embed(title='자동 차단 활성화', description='자동 차단 기능이 활성화되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
                elif situation == "비활성화":
                    await ctx.respond(embed=discord.Embed(title='자동 차단 비활성화', description='자동 차단 기능이 이미 비활성화되어있습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        else:
            # 상태가 없는 경우 기본값으로 설정
            if situation == "활성화":
                c.execute('INSERT INTO autoban_settings (guild_id, autoban_enabled) VALUES (?, ?)', (ctx.guild.id, 1))
                conn.commit()
                await ctx.respond(embed=discord.Embed(title='자동 차단 활성화', description='자동 차단 기능이 활성화되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
            elif situation == "비활성화":
                c.execute('INSERT INTO autoban_settings (guild_id, autoban_enabled) VALUES (?, ?)', (ctx.guild.id, 0))
                conn.commit()
                await ctx.respond(embed=discord.Embed(title='자동 차단 비활성화', description='자동 차단 기능이 비활성화되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
    else:
        await ctx.respond(embed=discord.Embed(title='에러', description='먼저 로그채널을 설정해주세요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))

@bot.event
async def on_member_join(member):
    c.execute('SELECT log_channel FROM log_channels WHERE guild_id=?', (member.guild.id,))
    result = c.fetchone()
    if result:
        log_channel_id = result[0]

        c.execute('SELECT autoban_enabled FROM autoban_settings WHERE guild_id=?', (member.guild.id,))
        autoban_result = c.fetchone()
        if autoban_result:
            autoban_enabled = bool(autoban_result[0])

            if autoban_enabled:
                c.execute('SELECT autoban_threshold FROM autoban_thresholds WHERE guild_id=?', (member.guild.id,))
                threshold_result = c.fetchone()
                if threshold_result:
                    autoban_threshold = threshold_result[0]
                    if autoban_threshold is None:
                        
                        await log_channel.send(embed=discord.Embed(title='에러', description="자동 차단 임계값이 설정되지 않았습니다. 관리자에게 문의하세요.", timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
                        return
                    join_date = member.created_at
                    current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
                    difference = current_time - join_date
                    threshold_timedelta = timedelta(days=autoban_threshold)

                    if difference < threshold_timedelta:
                        await member.ban(reason=f"계정 생성 후 {autoban_threshold}일이 지나지 않았습니다.")
                        with open('blacklist.txt', 'a') as file:
                            file.write(f"{member.id},{member.name}  {datetime.now()}\n")
                        print(f"{member}는 계정 생성 후 {autoban_threshold}일이 지나지 않아 차단되었습니다.")
                        c.execute('SELECT entry_exit_log_enabled FROM entry_exit_log_settings WHERE guild_id=?', (member.guild.id,))
                        entry_exit_log_result = c.fetchone()
                        if entry_exit_log_result:
                            entry_exit_log_enabled = bool(entry_exit_log_result[0])

                            if entry_exit_log_enabled:
                                log_channel = bot.get_channel(log_channel_id)
                                if log_channel:
                                    embed = discord.Embed(title="Spam Blocked", color=0xFF2D00)
                                    embed.add_field(name="User", value=member.mention, inline=False)
                                    embed.add_field(name="Account creation", value=difference, inline=False)
                                    embed.add_field(name="Result", value="Ban", inline=False)
                                    embed.add_field(name="Reason", value=f"계정 생성 후 {autoban_threshold}일이 지나지 않았습니다.", inline=False)
                                    embed.set_author(name=f"{member.name} {member.id}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
                                    embed.timestamp = datetime.utcnow()

                                    await log_channel.send(embed=embed)
                    else:
                        c.execute('SELECT entry_exit_log_enabled FROM entry_exit_log_settings WHERE guild_id=?', (member.guild.id,))
                        entry_exit_log_result = c.fetchone()
                        if entry_exit_log_result:
                            entry_exit_log_enabled = bool(entry_exit_log_result[0])

                            if entry_exit_log_enabled:
                                log_channel = bot.get_channel(log_channel_id)
                                if log_channel:                                    
                                    embed.add_field(name="User", value=member.mention, inline=False)
                                    embed.add_field(name="Account creation", value=difference, inline=False)
                                    embed.add_field(name="Result", value="Pass", inline=False)
                                    embed.set_author(name=f"{member.name} {member.id}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
                                    embed.timestamp = datetime.utcnow()
                                    await log_channel.send(embed=embed)
                else:
                    c.execute('SELECT entry_exit_log_enabled FROM entry_exit_log_settings WHERE guild_id=?', (member.guild.id,))
                    entry_exit_log_result = c.fetchone()
                    if entry_exit_log_result:
                        entry_exit_log_enabled = bool(entry_exit_log_result[0])

                        if entry_exit_log_enabled:                
                            log_channel = bot.get_channel(log_channel_id)
                            if log_channel:
                                embed = discord.Embed(title="UserJoin (Autoban Off)", color=0x62c1cc)
                                embed.add_field(name="User", value=member.mention, inline=False)
                                embed.add_field(name="Result", value="Pass", inline=False)
                                embed.set_author(name=f"{member.name} {member.id}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
                                embed.timestamp = datetime.utcnow()
                                await log_channel.send(embed=embed)
            else:
                c.execute('SELECT entry_exit_log_enabled FROM entry_exit_log_settings WHERE guild_id=?', (member.guild.id,))
                entry_exit_log_result = c.fetchone()
                if entry_exit_log_result:
                    entry_exit_log_enabled = bool(entry_exit_log_result[0])

                    if entry_exit_log_enabled:
                        log_channel = bot.get_channel(log_channel_id)
                        if log_channel:
                            embed = discord.Embed(title="UserJoin (Autoban Off)", color=0x62c1cc)
                            embed.add_field(name="User", value=member.mention, inline=False)
                            embed.add_field(name="Result", value="Pass", inline=False)
                            embed.set_author(name=f"{member.name} {member.id}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
                            embed.timestamp = datetime.utcnow()
                            await log_channel.send(embed=embed)
        else:
            # 자동 차단 기능 상태를 찾을 수 없는 경우 로그만 남기도록 수정
            pass
    else:
        # 로그 채널이 설정되지 않은 경우 로그만 남기도록 수정
        pass
@bot.slash_command(name="경고현황", description="유저의 경고를 확인합니다.")
async def check_warnings(ctx, user: discord.Member):
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return


    try:
        # 사용자의 경고 조회
        c.execute('SELECT warnings FROM warnings WHERE guild_id=? AND user_id=?', (ctx.guild.id, user.id))
        result = c.fetchone()
        total_warnings = result[0] if result else 0

        if total_warnings:
            await ctx.respond(embed=discord.Embed(title='경고 현황', description=f'{user.mention}님은 `{total_warnings}개`의 경고가 있습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        else:
            await ctx.respond(embed=discord.Embed(title='경고 현황', description=f'{user.mention}님은 경고가 없어요.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
    except Exception as e:
        error_message = f"An error occurred while checking warnings: {e}"
        print(error_message)
        await ctx.respond(error_message)
@bot.slash_command(name="내경고현황", description="자신의 경고를 확인합니다.")
async def check_my_warnings(ctx):
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    try:
        # 사용자의 경고 조회
        c.execute('SELECT warnings FROM warnings WHERE guild_id=? AND user_id=?', (ctx.guild.id, ctx.author.id))
        result = c.fetchone()
        total_warnings = result[0] if result else 0

        if total_warnings:
            await ctx.respond(embed=discord.Embed(title='경고 현황', description=f'{ctx.author.mention}님은 `{total_warnings}개`의 경고가 있습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        else:
            await ctx.respond(embed=discord.Embed(title='경고 현황', description=f'{ctx.author.mention}님은 경고가 없어요.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
    except Exception as e:
        error_message = f"An error occurred while checking warnings: {e}"
        print(error_message)
        await ctx.respond(error_message)
@bot.slash_command(name="경고초기화", description="유저의 경고를 초기화합니다.")
async def clearwarnings(ctx, user: discord.Member):
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return


    try:
        # 사용자의 경고 제거
        c.execute('DELETE FROM warnings WHERE guild_id=? AND user_id=?', (ctx.guild.id, user.id))
        conn.commit()

        await ctx.respond(embed=discord.Embed(title='경고 초기화', description=f'{user.mention}님의 경고가 초기화 되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
    except Exception as e:
        print(f"An error occurred: {e}")
        await ctx.respond("An error occurred while clearing warnings.")

@bot.slash_command(name= "로그",description="로그를 제어합니다.")
async def toggle_entry_exit_log(ctx, situation : Option(description='상태를 설정해주세요', choices=['활성화', '비활성화'],required=True)):
    
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return

    c.execute('SELECT log_channel FROM log_channels WHERE guild_id=?', (ctx.guild.id,))
    result = c.fetchone()
    if result:
        log_channel_id = result[0]

        c.execute('SELECT entry_exit_log_enabled FROM entry_exit_log_settings WHERE guild_id=?', (ctx.guild.id,))
        entry_exit_log_result = c.fetchone()
        if entry_exit_log_result:
            entry_exit_log_enabled = bool(entry_exit_log_result[0])

            if entry_exit_log_enabled:
                if situation == "활성화":
                    await ctx.respond(embed=discord.Embed(title='로그 활성화', description='로그기능이 이미 활성화되어있습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
                elif situation == "비활성화":
                    c.execute('UPDATE entry_exit_log_settings SET entry_exit_log_enabled=? WHERE guild_id=?', (0, ctx.guild.id))
                    conn.commit()
                    await ctx.respond(embed=discord.Embed(title='로그 비활성화', description='로그기능이 비활성화되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
            else:
                if situation == "활성화":
                    c.execute('UPDATE entry_exit_log_settings SET entry_exit_log_enabled=? WHERE guild_id=?', (1, ctx.guild.id))
                    conn.commit()

                    await ctx.respond(embed=discord.Embed(title='로그 활성화', description='로그기능이 활성화되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
                elif situation == "비활성화":
                    await ctx.respond(embed=discord.Embed(title='로그 비활성화', description='로그기능이 이미 비활성화되어있습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        else:
            if situation == "활성화":
                c.execute('INSERT INTO entry_exit_log_settings (guild_id, entry_exit_log_enabled) VALUES (?, ?)', (ctx.guild.id, 1))
                conn.commit()
                await ctx.respond(embed=discord.Embed(title='로그 활성화', description='로그기능이 활성화되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
            elif situation == "비활성화":
                c.execute('INSERT INTO entry_exit_log_settings (guild_id, entry_exit_log_enabled) VALUES (?, ?)', (ctx.guild.id,0))
                conn.commit()
                await ctx.respond(embed=discord.Embed(title='로그 비활성화', description='로그기능이 비활성화되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))

    else:
        await ctx.respond(embed=discord.Embed(title='에러', description='먼저 로그채널을 설정해주세요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
    


@bot.event
async def on_member_remove(member):
    c.execute('SELECT log_channel FROM log_channels WHERE guild_id=?', (member.guild.id,))
    result = c.fetchone()
    if result:
        c.execute('SELECT entry_exit_log_enabled FROM entry_exit_log_settings WHERE guild_id=?', (member.guild.id,))
        entry_exit_log_result = c.fetchone()
        if entry_exit_log_result:
            entry_exit_log_enabled = bool(entry_exit_log_result[0])

            if entry_exit_log_enabled:
                log_channel_id = result[0]
                log_channel = bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title="UserOut", color=0xFF0000)
                    embed.add_field(name="User", value=member.mention, inline=False)                              
                    embed.add_field(name="ServerOut time", value=datetime.utcnow(), inline=False)
                    embed.set_author(name=f"{member.name} {member.id}",icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
                    embed.timestamp = datetime.utcnow()
                    await log_channel.send(embed=embed)

@bot.slash_command(name= "로그채널",description="로그채널을 설정합니다.")
async def setlogchannel(ctx: commands.Context, channel: discord.TextChannel):
    # 관리자만 로그 채널 설정 가능

    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return

    c.execute('''INSERT OR REPLACE INTO log_channels (guild_id, log_channel)
                 VALUES (?, ?)''', (ctx.guild.id, channel.id))
    conn.commit()

    await ctx.respond(embed=discord.Embed(title='로그채널 설정', description=f'로그채널이 {channel.mention}으로 설정되었습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))

@bot.slash_command(name="유저차단일수",description="자동으로 차단할 유저 생성일을 지정합니다.")
async def set_autoban_threshold(ctx: commands.Context, days: int):
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if days <= 0:
        await ctx.respond(embed=discord.Embed(title='숫자에러', description='양수를 입력해주세요.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return

    c.execute(
        '''INSERT OR REPLACE INTO autoban_settings (guild_id, autoban_enabled) VALUES (?, ?)''',
        (ctx.guild.id, 1)
    )
    conn.commit()

    c.execute(
        '''INSERT OR REPLACE INTO autoban_thresholds (guild_id, autoban_threshold) VALUES (?, ?)''',
        (ctx.guild.id, days)
    )
    conn.commit()

    await ctx.respond(embed=discord.Embed(title='설정완료', description=f'자동차단일수가 {days}일로 설정되었습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))

@bot.slash_command(name="경고",description="유저에게 경고를 줍니다 5회시 차단")
async def warn_user(ctx: commands.Context, member: discord.Member, *, reason: str , warntimes: int):
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return


    try:
        # 누적된 경고 수 조회
        c.execute('SELECT warnings FROM warnings WHERE guild_id=? AND user_id=?', (ctx.guild.id, member.id))
        result = c.fetchone()
        total_warnings = result[0] if result else 0

        if total_warnings > 0:
            # 이미 경고가 있는 경우, 경고 회수만 증가
            c.execute('UPDATE warnings SET warnings=? WHERE guild_id=? AND user_id=?', (total_warnings + warntimes, ctx.guild.id, member.id))
            if total_warnings >= 5:
                # 경고가 5회 이상인 경우, 사용자 강퇴
                await member.ban(reason=f"경고 5회 누적으로 인한 차단")
                await ctx.respond(f"{member.mention} 님은 경고가 5회 누적되어 강퇴되었습니다.")
        else:
            # 경고가 없는 경우, 새로운 경고 추가
            c.execute('''INSERT INTO warnings (guild_id, user_id, warnings, reason, timestamp)
                         VALUES (?, ?, ?, ?, ?)''', (ctx.guild.id, member.id, warntimes, reason, datetime.utcnow().isoformat()))

        conn.commit()
        if 5-(total_warnings + warntimes) <= 0:
            aa = f"경고 누적으로 인해 차단 되었습니다"
        else:
            aa = f"차단까지 남은 경고수 `{5-(total_warnings + warntimes)}회`"
        await ctx.respond(embed=discord.Embed(title="경고 부여", description=f'{member.mention} 님에 대한 경고가 부여되었습니다.\n사유: {reason}\n처리자: {ctx.author.mention}\n누적 경고 수: `{total_warnings + warntimes}회`  {aa}', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))

    except Exception as e:
        # 다른 예외를 처리
        print(f"오류가 발생했습니다: {e}")
        await ctx.respond("경고 처리 중에 오류가 발생했습니다.")

@bot.slash_command(name= "핑",description="퐁을 말합니다.")
async def ping(ctx):
    start = time.perf_counter()
    pings = bot.latency * 1000
    if pings < 100:
        pinglevel = '🔵 매우좋음'
    elif pings < 300: 
        pinglevel = '🟢 양호함'
    elif pings < 400: 
        pinglevel = '🟡 보통'
    elif pings < 6000: 
        pinglevel = '🔴 나쁨'
    else: 
        pinglevel = '⚪ 매우나쁨'
    end = time.perf_counter()
    duration = (end - start) * 1000
    if duration < 100:
        pinglevels = '🔵 매우좋음'
    elif duration < 300: 
        pinglevels = '🟢 양호함'
    elif duration < 400: 
        pinglevels = '🟡 보통'
    elif duration < 6000: 
        pinglevels = '🔴 나쁨'
    else: 
        pinglevels = '⚪ 매우나쁨'

    await ctx.respond(embed=discord.Embed(title="🏓 퐁!", description='봇 메세지 지연시간 : `{:.2f} ms` -'.format(duration)  + f' {pinglevels}'+
                                        '\n디스코드 지연시간 : `{:.2f} ms` -'.format(pings)+
                                        f'{pinglevel}\n{bot.user.name}  v{key.VERSION}', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
message_count = {}

# 스팸 감지에 사용할 상수 값
SPAM_THRESHOLD = 6  # 일정 시간 동안의 최대 허용 메시지 수
SPAM_SECONDS = 5 # 일정 시간 (초) 동안

@bot.slash_command(name="도배금지", description="서버의 도배 금지 기능을 토글합니다.")
async def toggle_anti_spam(ctx, situation : Option(description='상태를 설정해주세요', choices=['활성화', '비활성화'],required=True)):
    # Check for administrator permissions
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return

    # Toggle anti-spam feature for the server
    c.execute('SELECT anti_spam_enabled FROM spam_prevention_settings WHERE guild_id=?', (ctx.guild.id,))
    result = c.fetchone()

    if result:
        anti_spam_enabled = bool(result[0])
        if anti_spam_enabled:
            if situation == "활성화":
                await ctx.respond(embed=discord.Embed(title='도배 금지 활성화', description='도배 금지 기능이 이미 활성화되었습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
            elif situation == "비활성화":
                c.execute('UPDATE spam_prevention_settings SET anti_spam_enabled=? WHERE guild_id=?', (0, ctx.guild.id))
                conn.commit()
                await ctx.respond(embed=discord.Embed(title='도배 금지 비활성화', description='도배 금지 기능이 비활성화되었습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        else:
            if situation == "활성화":
                c.execute('UPDATE spam_prevention_settings SET anti_spam_enabled=? WHERE guild_id=?', (1, ctx.guild.id))
                conn.commit()

                await ctx.respond(embed=discord.Embed(title='도배 금지 활성화', description='도배 금지 기능이 활성화되었습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
            elif situation == "비활성화":
                await ctx.respond(embed=discord.Embed(title='도배 금지 비활성화', description='도배 금지 기능이 이미 비활성화되었습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
    else:
            if situation == "활성화":
                c.execute('INSERT INTO spam_prevention_settings (guild_id, anti_spam_enabled) VALUES (?, ?)', (ctx.guild.id, 1))
                conn.commit()
                await ctx.respond(embed=discord.Embed(title='도배 금지 활성화', description='도배 금지 기능이 활성화되었습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
            elif situation == "비활성화":
                c.execute('INSERT INTO spam_prevention_settings (guild_id, anti_spam_enabled) VALUES (?, ?)', (ctx.guild.id,0))
                conn.commit()
                await ctx.respond(embed=discord.Embed(title='도배 금지 비활성화', description='도배 금지 기능이 비활성화되었습니다', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))

@bot.event
async def on_message(message):
    # 봇의 메시지는 무시
    if message.author.bot:
        return

    # 서버마다 스팸 감지 상태 확인
    c.execute('SELECT anti_spam_enabled FROM spam_prevention_settings WHERE guild_id=?', (message.guild.id,))
    result = c.fetchone()
    spam_detection_enabled = bool(result[0]) if result else True  # Default to True if not found

    # 스팸 감지가 비활성화되어 있는 경우
    if not spam_detection_enabled:
        await bot.process_commands(message)
        return

    # 메시지를 보낸 사용자의 ID를 가져옴
    user_id = message.author.id

    # 사용자의 메시지 카운트를 확인하고 초기화
    count = message_count.get(user_id, 0)
    count += 1
    message_count[user_id] = count

    # 일정 시간 동안의 메시지 수가 스팸 임계값을 초과하는 경우
    if count > SPAM_THRESHOLD:
        message_count[user_id] = 0
        reason="도배"
        c.execute('SELECT warnings FROM warnings WHERE guild_id=? AND user_id=?', (message.guild.id, message.author.id))
        result = c.fetchone()
        total_warnings = result[0] if result else 0

        if total_warnings > 0:
            # 이미 경고가 있는 경우, 경고 회수만 증가
            c.execute('UPDATE warnings SET warnings=? WHERE guild_id=? AND user_id=?', (total_warnings + 1, message.guild.id, user_id))
            if total_warnings >= 5:
                # 경고가 5회 이상인 경우, 사용자 강퇴
                await message.author.ban(reason=f"경고 5회 누적으로 인한 차단")
                await message.channel.send(f"{message.author.mention} 님은 경고가 5회 누적되어 강퇴되었습니다.")
        else:
            # 경고가 없는 경우, 새로운 경고 추가
            c.execute('''INSERT INTO warnings (guild_id, user_id, warnings, reason, timestamp)
                         VALUES (?, ?, ?, ?, ?)''', (message.guild.id, user_id, 1, reason, datetime.utcnow().isoformat()))
        conn.commit()
        if 5-(total_warnings + 1) <= 0:
            aa = f"경고 누적으로 인해 차단 되었습니다"
        else:
            aa = f"차단까지 남은 경고수 `{5-(total_warnings + 1)}회`"
        await message.channel.send(embed=discord.Embed(title="경고 부여", description=f'{message.author.mention} 님에 대한 경고가 부여되었습니다.\n사유: {reason}\n누적 경고 수: `{total_warnings + 1}회`  {aa}', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
    # 지정된 시간 후에 메시지 카운트를 초기화
    await asyncio.sleep(SPAM_SECONDS)
    message_count[user_id] = 0

    # 원래의 on_message 이벤트를 호출하여 다른 이벤트 핸들러들이 실행되도록 함
    await bot.process_commands(message)
@bot.slash_command(name="경고제거",description="유저에게 경고를 1을 제거합니다")
async def warn_user(ctx: commands.Context, member: discord.Member):
    # Check for administrator permissions
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.administrator :
        await ctx.respond(embed=discord.Embed(title='권한부족', description='관리자만 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return


    try:
        # 누적된 경고 수 조회
        c.execute('SELECT warnings FROM warnings WHERE guild_id=? AND user_id=?', (ctx.guild.id, member.id))
        result = c.fetchone()
        total_warnings = result[0] if result else 0

        if total_warnings > 0:
            # 이미 경고가 있는 경우, 경고 회수만 증가
            c.execute('UPDATE warnings SET warnings=? WHERE guild_id=? AND user_id=?', (total_warnings -1, ctx.guild.id, member.id))

        else:
            # 경고가 없는 경우, 새로운 경고 추가
            await ctx.respond(embed=discord.Embed(title='경고제거', description=f'{member.mention}님에 대한 경고가 없습니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))

        conn.commit()
        await ctx.respond(embed=discord.Embed(title='경고제거', description=f'{member.mention} 님에 대한 경고가 제거되었습니다.\n처리자: {ctx.author.mention}\n누적 경고 수: `{total_warnings-1 }회` 차단까지 남은 경고수 `{5-(total_warnings + -1)}회`', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))

    except Exception as e:
        # 다른 예외를 처리
        print(f"오류가 발생했습니다: {e}")
        await ctx.respond("경고 처리 중에 오류가 발생했습니다.")
@bot.slash_command(name="청소", description="지정된 수만큼 메시지를 삭제합니다.")
async def clear_messages(ctx, amount: int):
    # Check for administrator permissions
    if ctx.guild is None:  # 메시지가 DM인 경우
        await ctx.respond(embed=discord.Embed(title='에러', description='DM에서 지원하지 않는 기능입니다.', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    if is_bot_owner(ctx):
        pass
    elif not ctx.author.guild_permissions.manage_messages:
        await ctx.respond(embed=discord.Embed(title='권한부족', description='메세지 관리 권한이 있어야 사용할 수 있어요', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
        return
    try:
        deleted = await ctx.channel.purge(limit=amount )
        await ctx.respond(embed=discord.Embed(title='청소', description=f'`{len(deleted) }개`의 메세지를 제거 했어요!', timestamp=datetime.now(pytz.timezone('UTC')),color=0xFFFF00))
    except Exception as e:
        await ctx.respond(f"메시지 삭제 중 오류가 발생했습니다: {e}", hidden=True)
@bot.slash_command(name="정보", description="Spam의 정보를 확인인합니다.")
async def info(ctx):
    current_time = time.time()
    uptime_seconds = current_time - start_time
    s_seconds = start_time
    
    # 초를 다시 시간, 분, 초로 변환
    uptime_minutes, uptime_seconds = divmod(uptime_seconds, 60)
    uptime_hours, uptime_minutes = divmod(uptime_minutes, 60)
    uptime_days, uptime_hours = divmod(uptime_hours, 24)

    if(bot.owner_id == ctx.author.id):
        await ctx.response("text admin")
        return
    embed = discord.Embed(title="정보", color=0xFFFF00)
    embed.add_field(name="업타임", value=f"{int(uptime_days)}일 {int(uptime_hours)}시간 {int(uptime_minutes)}분 {int(uptime_seconds)}초    ", inline=True)                              
    embed.add_field(name="버전", value=f"V{key.VERSION}", inline=True)
    embed.add_field(name="개발팀", value=f"팀 스팸블랙리스트", inline=True)
    embed.add_field(name="마지막 업데이트", value=f"{formatted_datetime}", inline=True)
    embed.add_field(name="차단된 스팸 유저수", value=f"{count_lines('blacklist.txt')}명", inline=True)
    embed.add_field(name="호스팅 디바이스", value="Mac Pro(M2 Ultra), MacBook Pro 16(M3 Max)으로 호스팅되고 있습니다.", inline=False)
    embed.add_field(name="데이터 서버 디바이스", value="Ubuntu 22.04으로 호스팅되고 있습니다.", inline=False)
    embed.add_field(name="",value="[봇 초대하기](https://discord.com/api/oauth2/authorize?client_id=1195649127489478676&permissions=8&scope=bot)", inline=False)
    embed.add_field(name="",value="[스팸봇 공식서버](https://discord.gg/HwyX7rxjKE)", inline=True)
    embed.add_field(name="",value="[이용약관](https://ubiquitous-hamster-bda179.netlify.app/tos)", inline=True)
    embed.add_field(name="",value="[개인정보 처리 방침](https://ubiquitous-hamster-bda179.netlify.app/policy)", inline=True)
    embed.timestamp = datetime.utcnow()
    await ctx.respond(embed=embed)

if(key.DEBUG):
    bot.run(key.DEBUG_TOKEN)
else:
    bot.run(key.TOKEN)