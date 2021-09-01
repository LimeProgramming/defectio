import defectio

client = defectio.Client()


@client.event
async def on_ready():
    print("We have logged in.")


@client.event
async def on_message(message: defectio.Message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")


client.run(
    session_token="session_token",
    user_id="user_id",
)
