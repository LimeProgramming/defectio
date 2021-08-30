# Defectio

![revolt-api](https://img.shields.io/npm/v/revolt-api?label=Revolt%20API)[![Documentation Status](https://readthedocs.org/projects/defectio/badge/?version=latest)](https://defectio.readthedocs.io/en/latest/?badge=latest)

**defectio** is a direct implementation of the entire Revolt API and provides a way to authenticate and start communicating with Revolt servers. It is currently in active development so not all features are yet implemented. Similar interface to discord.py

## Example Usage

```python3
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


client.run("")
```

## Contribute

Join our server [here](https://app.revolt.chat/invite/FfbwgFDk)
