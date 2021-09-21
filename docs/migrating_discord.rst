Migrating from discord
======================

If you are coming from discord bot development there is a large similarity with this library and discord.py.
The overall structure and behaviour of the library is similar allowing a nearly seamless transition.

Due to differences between Revolt and Discord a couple things have changed in behaviour and naming.

Guild is now Server
~~~~~~~~~~~~~~~~~~~~~

The official API documentation calls the "Server" concept a "Server" instead of how Discord handles it.

A list of differences is as follows:

+-------------------------------+----------------------------------+
|             Discord           |              Revolt              |
+-------------------------------+----------------------------------+
| ``Message.guild``             | :attr:`Message.server`           |
+-------------------------------+----------------------------------+
| ``GuildChannel.guild``        | :attr:`.ServerChannel.server`    |
+-------------------------------+----------------------------------+
| ``Client.guilds``             | :attr:`Client.servers`           |
+-------------------------------+----------------------------------+
| ``Client.get_guild``          | :meth:`Client.get_server`        |
+-------------------------------+----------------------------------+
| ``Role.guild``                | :attr:`Role.server`              |
+-------------------------------+----------------------------------+
| ``Invite.guild``              | :attr:`Invite.server`            |
+-------------------------------+----------------------------------+
| ``Member.guild``              | :attr:`Member.server`            |
+-------------------------------+----------------------------------+
| ``Permissions.manage_guild``  | :attr:`Permissions.manage_server`|
+-------------------------------+----------------------------------+
| ``Client.create_guild``       | :meth:`Client.create_server`     |
+-------------------------------+----------------------------------+

Self Bots
~~~~~~~~~~~~~~~~~~~~~

Unlike Discord, self bots are allowed and are to a certain extent encouraged. These can be used to enhance and customise
your Revolt experience. You have the option to login as a user or as a bot the two are functionality identical. The 
different connection methods are as follows:

    .. code-block:: python

        # Login as a user
        client = Client().run(
            session_token="session_token",
            user_id="user_id"
        )

        # Login as a bot
        client = Client().run("bot_token")

