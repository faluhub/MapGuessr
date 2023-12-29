import discord, os, dotenv, maps
from discord import ApplicationContext, option
from discord.ext import tasks
from discord.utils import basic_autocomplete
from database.classes import User, Guild
from datetime import datetime, timedelta

dotenv.load_dotenv()
bot = discord.AutoShardedBot(
    intents=discord.Intents.default(),
    # debug_guilds=[1018128160962904114]
)
start = datetime.now()

location: maps.Location = None

@tasks.loop(minutes=30)
async def challenge_loop():
    bot.change_presence(activity=discord.Game("Country Challenge", timestamps={"end": datetime.now() + timedelta(minutes=30)}))
    global location
    channels = Guild.get_all_channels()
    if len(channels) == 0:
        return
    path = "./data/challenge.jpg"
    location = maps.gen_country()
    location.image.save(path, format="jpeg")
    embed = discord.Embed(
        title="New Country",
        description="Make your guess using `/guess`!",
        color=discord.Color.green()
    )
    for channel_id in channels:
        channel = bot.get_channel(channel_id)
        try:
            return await channel.send(embed=embed, file=discord.File(path))
        except:
            continue

@bot.event
async def on_connect():
    await bot.register_commands()
    if bot.auto_sync_commands:
        await bot.sync_commands()
    print("Connected")

@bot.event
async def on_ready():
    challenge_loop.start()
    print(f"Ready, took {(datetime.now() - start).seconds} seconds.")

@bot.slash_command(name="guess", description="Make your guess")
@option(
    name="country",
    type=str,
    description="The country",
    autocomplete=basic_autocomplete(maps.get_country_names())
)
async def guess_cmd(ctx: ApplicationContext, country: str):
    await ctx.defer(ephemeral=True)
    user_db = User(ctx.author.id)
    if location == None:
        return await ctx.followup.send("There is no country to guess right now!")
    if user_db.has_guessed():
        return await ctx.followup.send("You've already made a guess for this location!")
    correct = location.country == country
    user_db.increment_guesses(correct)
    embed = None
    if correct:
        embed = discord.Embed(
            description=f"{country} is correct!\nYou now have {user_db.get_correct()} total correct guesses!",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            description="That's incorrect.\nYou will no longer be able to guess for this challenge. :(",
            color=discord.Color.red()
        )
    await ctx.followup.send(embed=embed)

@bot.slash_command(name="user", description="View a user's stats")
@option(
    name="member",
    type=discord.Member,
    description="The user whose stats you want to view",
    required=False
)
async def user_cmd(ctx: ApplicationContext, member: discord.Member):
    await ctx.defer()
    user = ctx.author if member is None else member
    user_db = User(user.id)
    guesses = user_db.get_guesses()
    correct = user_db.get_correct()
    rate = round(correct / guesses * 100, 1)
    embed = discord.Embed(color=discord.Color.green())
    embed.set_author(name=user.name, icon_url=user.avatar.url)
    embed.add_field(name="Guesses Made:", value=f"`{guesses}`", inline=False)
    embed.add_field(name="Correct Guesses:", value=f"`{correct}`", inline=False)
    embed.add_field(name="Success Rate:", value=f"`{rate}%`", inline=False)
    return await ctx.followup.send(embed=embed)

@bot.slash_command(name="channel", description="Change the channel in which the challenge will be sent")
@discord.default_permissions(manage_channels=True)
@option(
    name="channel",
    type=discord.TextChannel,
    description="The channel in which the challenge will be sent",
    required=False
)
async def channel_cmd(ctx: ApplicationContext, channel: discord.TextChannel):
    await ctx.defer(ephemeral=True)
    guild_db = Guild(ctx.guild.id)
    if channel is None:
        embed = discord.Embed(
            description="The channel has been removed. :(",
            color=discord.Color.red()
        )
        guild_db.remove_channel()
        return await ctx.followup.send(embed=embed)
    embed = discord.Embed(
        description=f"The channel has been set to <#{channel.id}>!",
        color=discord.Color.green()
    )
    guild_db.set_channel(channel.id)
    return await ctx.followup.send(embed=embed)

def run():
    bot.run(os.environ["DISCORD_TOKEN"])
