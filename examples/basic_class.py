import defectio


class MyClient(defectio.Client):
    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))

    async def on_message(self, message: defectio.Message):
        print("Message from {0.author}: {0.content}".format(message))


client = MyClient()

client.run("bot_token")
