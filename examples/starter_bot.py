import defectio


class MyClient(defectio.Client):
    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))

    async def on_message(self, message: defectio.Message):
        if message.author == self.user:
            return
        if message.content.startswith("$delete"):
            await message.channel.send(
                "Will delete this message in 5 seconds.", delete_after=5
            )
        elif message.content.startswith("$hello"):
            await message.channel.send("Hello!")
        elif message.content.startswith("$echo"):
            await message.channel.send(message.content[5:])
        elif message.content.startswith("$sleep"):
            message = await message.channel.send("Sleeping for 5 seconds...")
            await asyncio.sleep(5)
            await message.edit("Done sleeping.")
        elif message.content.startswith("$help"):
            await message.channel.send(
                "I can do the following:\n"
                "\$delete - delete this message in 5 seconds\n"
                "\$hello - say hello\n"
                "\$echo - echo the message you send\n"
                "\$sleep - sleep for 5 seconds\n"
                "\$help - this help message\n"
            )

    async def on_message_edit(
        self, older_message: defectio.Message, newer_message: defectio.Message
    ):
        print("Message edited: {0.content}".format(newer_message))


client = MyClient()

client.run("bot_token")
