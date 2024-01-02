import discord, os, dotenv, maps, traceback, sys
from discord import ApplicationContext, option
from discord.ext import tasks
from discord.utils import basic_autocomplete
from database.classes import User, Guild, Guess
from datetime import datetime, timedelta

dotenv.load_dotenv()
debug = bool(os.environ.get("DEBUG", False))
debug_guild = 1018128160962904114
bot = discord.AutoShardedBot(
    intents=discord.Intents.default(),
    debug_guilds=[debug_guild] if debug else None,
    owner_ids=[810863994985250836]
)
start: datetime = datetime.now()

location: maps.Location = maps.get_old_location()
generating = False
generated_at: datetime = None

@tasks.loop(seconds=1)
async def start_challenge_loop():
    if challenge_loop.is_running():
        return
    now = datetime.now().minute
    if now == 0 or now == 30:
        challenge_loop.start()
        print("Started challenge event loop")
        start_challenge_loop.cancel()

@tasks.loop(minutes=30)
async def challenge_loop():
    global location, generating, generated_at, debug

    if generating:
        return
    generating = True

    last = ""
    if not location is None:
        last = f"\nThe last country was `{location.country}`."
        total_guesses = Guess.get_total_guesses()
        guesses = Guess.get_all_guesses()
        if not total_guesses is None and not guesses is None:
            if not len(last) == 0:
                last += "\n\n"
            last += "*Top 5 guessed countries from last challenge:*\n"
            rank = 0
            for guess in guesses:
                rank += 1
                country, amount = guess
                rate = round(amount / total_guesses * 100, 1)
                emoji = "✅" if country.lower() == location.country.lower() else "❌"
                last += f"**{rank}.** *{country.capitalize()}* {emoji} - `{amount}` *({rate}%)*\n"

    User.reset_guessed()
    Guess.clear_guesses()

    location = maps.gen_country()
    generated_at = datetime.now()

    path = "./data/challenge.jpg"
    location.image.save(path, format="jpeg")

    embed = discord.Embed(
        title="Country Challenge",
        description="Make your guess using `/guess`!" + last,
        color=discord.Color.green(),
        timestamp=generated_at
    )
    embed.set_footer(text=f"Google ©️{location.year}")

    channels = Guild.get_all_channels()
    for channel_id in channels:
        channel = bot.get_channel(channel_id)
        if not channel is None:
            try:
                await channel.send(embed=embed, file=discord.File(path))
            except:
                pass

    generating = False

@tasks.loop(seconds=10)
async def status_loop():
    if not challenge_loop.is_running():
        return await bot.change_presence(activity=discord.Game("Waiting to restart..."))

    if challenge_loop.next_iteration is None:
        return

    diff: timedelta = challenge_loop.next_iteration.replace(tzinfo=None) - datetime.now()
    value = max(0, int(round(diff.seconds / 60)))

    message = f"{value} Minute{'s' if not value == 1 else ''} Left..." if not value == 0 else "Generating New Challenge..."
    return await bot.change_presence(activity=discord.Game(message))

@bot.event
async def on_connect():
    global start

    await bot.register_commands()
    if bot.auto_sync_commands:
        await bot.sync_commands()

    print(f"Connected, took {(datetime.now() - start).seconds} second(s).")

@bot.event
async def on_ready():
    global start

    start_challenge_loop.start()
    status_loop.start()

    print(f"Ready, took {(datetime.now() - start).seconds} second(s).")

@bot.event
async def on_error(event: str, *args, **kwargs):
    _, error, _ = sys.exc_info()
    if isinstance(error, discord.errors.NotFound):
        return
    traceback.print_exc()

@bot.event
async def on_application_command_error(_: ApplicationContext, error: Exception):
    if isinstance(error, discord.errors.NotFound):
        return
    print("".join(traceback.format_exception(type(error), error, error.__traceback__)))

@bot.slash_command(name="guess", description="Make your guess")
@option(
    name="country",
    type=str,
    description="The country",
    autocomplete=basic_autocomplete(maps.get_country_names())
)
async def guess_cmd(ctx: ApplicationContext, country: str):
    global location

    await ctx.defer(ephemeral=True)

    user_db = User(ctx.author.id)

    if location is None:
        return await ctx.followup.send("There is no country to guess right now!\nIf a challenge was sent previously, you might be getting this error because the bot has been restarted.")
    if user_db.has_guessed():
        return await ctx.followup.send("You've already made a guess for this location!")
    if not country in maps.get_country_names():
        return await ctx.followup.send("That is not a valid country!")

    correct = location.country.lower() == country.lower()
    Guess(country.lower()).increment()
    user_db.increment_guesses(correct)

    if correct:
        embed = discord.Embed(
            description=f"`{country.lower().capitalize()}` is correct!\nYou now have {user_db.get_correct()} total correct guesses!",
            color=discord.Color.green()
        )
        return await ctx.followup.send(embed=embed)

    embed = discord.Embed(
        description=f"{country.lower().capitalize()} is incorrect.\nYou will no longer be able to guess for this challenge. :(",
        color=discord.Color.red()
    )
    return await ctx.followup.send(embed=embed)

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
        guild_db.remove_channel()

        embed = discord.Embed(
            description="The channel has been removed. :(",
            color=discord.Color.red()
        )
        return await ctx.followup.send(embed=embed)

    guild_db.set_channel(channel.id)

    embed = discord.Embed(
        description=f"The channel has been set to <#{channel.id}>!",
        color=discord.Color.green()
    )
    return await ctx.followup.send(embed=embed)

@bot.slash_command(name="leaderboard", description="Show who has the most correct guesses")
@option(
    name="amount",
    type=int,
    description="The amount of users to be fetched",
    required=False
)
async def leaderboard_cmd(ctx: ApplicationContext, amount: int):
    await ctx.defer()

    amount = 5 if amount is None else amount

    users = User.get_top_correct(amount)

    leaderboard = ""
    rank = 0
    for user in users:
        user_id, guesses, correct = user
        user = await bot.get_or_fetch_user(user_id)
        if not user is None:
            rank += 1
            rate = round(correct / guesses * 100, 1)
            leaderboard += f"**{rank}.** *{user.name}* - `{correct}/{guesses}` *({rate}%)*\n"

    if len(leaderboard) == 0:
        embed = discord.Embed(
            description="The leaderboard couldn't be processed.",
            color=discord.Color.red()
        )
        return await ctx.followup.send(embed=embed)

    embed = discord.Embed(
        title=f"Top {min(amount, len(users))} Players",
        description=leaderboard,
        color=discord.Color.green()
    )
    return await ctx.followup.send(embed=embed)

@bot.slash_command(name="next", description="Skips to the next challenge", guild_ids=[debug_guild])
async def next_cmd(ctx: ApplicationContext):
    await ctx.defer()
    if not ctx.author.id in bot.owner_ids:
        return await ctx.followup.send("You have to be an owner of the bot to be able to run this command.")
    await challenge_loop.coro()
    return await ctx.followup.send("Skipped to next challenge.")

def run():
    bot.run(os.environ["DISCORD_TOKEN"])
