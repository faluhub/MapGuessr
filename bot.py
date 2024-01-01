import discord, os, dotenv, maps, traceback
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
generating = False
generated_at = None

@tasks.loop(minutes=30)
async def challenge_loop():
    global location, generating, generated_at
    if generating:
        return
    generating = True
    User.reset_guessed()
    channels = Guild.get_all_channels()
    path = "./data/challenge.jpg"
    last = ""
    if not location is None:
        last = f"\nThe last country was `{location.country}`."
    location = maps.gen_country()
    generated_at = datetime.now()
    location.image.save(path, format="jpeg")
    embed = discord.Embed(
        title="Country Challenge",
        description="Make your guess using `/guess`!" + last,
        color=discord.Color.green(),
        timestamp=generated_at
    )
    embed.set_footer(text=f"Google ©️{location.year}")
    for channel_id in channels:
        channel = bot.get_channel(channel_id)
        try:
            await channel.send(embed=embed, file=discord.File(path))
        except:
            traceback.print_exc()
    generating = False

@tasks.loop(seconds=10)
async def status_loop():
    if challenge_loop.next_iteration is None:
        return
    diff: timedelta = challenge_loop.next_iteration.replace(tzinfo=None) - datetime.now()
    hours = diff.seconds / 60 > 60
    value = max(0, int(round(diff.seconds / 60 / 60 if hours else diff.seconds / 60)))
    message = f"{value} {'Hour' if hours else 'Minute'}{'s' if not value == 1 else ''} Left..." if not value == 0 else "Generating New Challenge..."
    return await bot.change_presence(activity=discord.Game(message))

@bot.event
async def on_connect():
    await bot.register_commands()
    if bot.auto_sync_commands:
        await bot.sync_commands()
    print("Connected")

@bot.event
async def on_ready():
    challenge_loop.start()
    status_loop.start()
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
    correct = location.country.lower() == country.lower()
    user_db.increment_guesses(correct)
    embed = None
    if correct:
        embed = discord.Embed(
            description=f"`{country}` is correct!\nYou now have {user_db.get_correct()} total correct guesses!",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            description="That's incorrect.\nYou will no longer be able to guess for this challenge. :(",
            color=discord.Color.red()
        )
    await ctx.followup.send(embed=embed)

@bot.slash_command(name="send", description="Re-send the ongoing challenge")
async def send_cmd(ctx: ApplicationContext):
    global generating, generated_at
    await ctx.defer()
    if generating:
        embed = discord.Embed(
            description="A new challenge is being generated right now, so you cannot use this command.",
            color=discord.Color.red()
        )
        return await ctx.followup.send(embed=embed)
    embed = discord.Embed(
        title="Country Challenge",
        description="Make your guess using `/guess`!",
        color=discord.Color.green(),
        timestamp=generated_at
    )
    embed.set_footer(text=f"Google ©️{location.year}")
    return await ctx.followup.send(embed=embed, file=discord.File("./data/challenge.jpg"))

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
    if not user_db.exists():
        embed = discord.Embed(
            description="This user hasn't played yet.",
            color=discord.Color.red()
        )
        return await ctx.followup.send(embed=embed)
    guesses = user_db.get_guesses()
    correct = user_db.get_correct()
    rate = round(correct / guesses * 100, 1)
    embed = discord.Embed(color=discord.Color.green())
    embed.set_author(name=user.name, icon_url=None if user.avatar is None else user.avatar.url)
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
