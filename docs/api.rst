.. currentmodule:: defectio

API Reference
===============

The following section outlines the API of defectio.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way.  If the logging module is not configured,
    these logs will not be output anywhere.  See :ref:`logging_setup` for
    more information on how to set up and use the logging module with
    defectio.

Version Related Info
---------------------

There are two main ways to query version information about the library.

.. data:: version_info

    A named tuple that is similar to :obj:`py:sys.version_info`.

    Just like :obj:`py:sys.version_info` the valid values for ``releaselevel`` are
    'alpha', 'beta', 'candidate' and 'final'.

.. data:: __version__

    A string representation of the version. e.g. ``'1.0.0rc1'``. This is based
    off of :pep:`440`.

Clients
--------

Client
~~~~~~~

.. attributetable:: Client

.. autoclass:: Client
    :members:

.. _defectio-api-events:

Event Reference
---------------

This section outlines the different types of events listened by :class:`Client`.

There are two ways to register an event, the first way is through the use of
:meth:`Client.event`. The second way is through subclassing :class:`Client` and
overriding the specific events. For example: ::

    import defectio

    class MyClient(defectio.Client):
        async def on_message(self, message):
            if message.author == self.user:
                return

            if message.content.startswith('$hello'):
                await message.channel.send('Hello World!')

If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignoring the exception.

.. warning::

    All the events must be a |coroutine_link|_. If they aren't, then you might get unexpected
    errors. In order to turn a function into a coroutine they must be ``async def``
    functions.

.. function:: on_ready()

    Called when the client is done preparing the data received from Revolt. Usually after login is successful.

    .. warning::

        This function is not guaranteed to be the first event called.
        Likewise, this function is **not** guaranteed to only be called
        once. This library implements reconnection logic and thus will
        end up calling this event whenever a RESUME request fails.

.. function:: on_error(event, *args, **kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    printed to stderr and the exception is ignored. If you want to
    change this behaviour and handle the exception for whatever reason
    yourself, this event can be overridden. Which, when done, will
    suppress the default action of printing the traceback.

    The information of the exception raised and the exception itself can
    be retrieved with a standard call to :func:`sys.exc_info`.

    If you want exception to propagate out of the :class:`Client` class
    you can define an ``on_error`` handler consisting of a single empty
    :ref:`raise statement <py:raise>`. Exceptions raised by ``on_error`` will not be
    handled in any way by :class:`Client`.

    :param event: The name of the event that raised the exception.
    :type event: :class:`str`

    :param args: The positional arguments for the event that raised the
        exception.
    :param kwargs: The keyword arguments for the event that raised the
        exception.

.. function:: on_socket_raw_receive(msg)

    Called whenever a message is received from the WebSocket, before
    it's processed. This event is always dispatched when a message is
    received and the passed data is not processed in any way.

    This is only really useful for grabbing the WebSocket stream and
    debugging purposes.

    .. note::

        This is only for the messages received from the client
        WebSocket. The voice WebSocket will not trigger this event.

    :param msg: The message passed in from the WebSocket library.
                Could be :class:`bytes` for a binary message or :class:`str`
                for a regular message.
    :type msg: Union[:class:`bytes`, :class:`str`]

.. function:: on_socket_raw_send(payload)

    Called whenever a send operation is done on the WebSocket before the
    message is sent. The passed parameter is the message that is being
    sent to the WebSocket.

    This is only really useful for grabbing the WebSocket stream and
    debugging purposes.

    .. note::

        This is only for the messages sent from the client
        WebSocket. The voice WebSocket will not trigger this event.

    :param payload: The message that is about to be passed on to the
                    WebSocket library. It can be :class:`bytes` to denote a binary
                    message or :class:`str` to denote a regular text message.

.. function:: on_typing(channel, user, when)

    Called when someone begins typing a message.

    The ``channel`` parameter can be a :class:`abc.Messageable` instance.
    Which could either be :class:`TextChannel`, :class:`GroupChannel`, or
    :class:`DMChannel`.

    If the ``channel`` is a :class:`TextChannel` then the ``user`` parameter
    is a :class:`Member`, otherwise it is a :class:`User`.

    :param channel: The location where the typing originated from.
    :type channel: :class:`abc.Messageable`
    :param user: The user that started typing.
    :type user: Union[:class:`User`, :class:`Member`]
    :param when: When the typing started as a naive datetime in UTC.
    :type when: :class:`datetime.datetime`

.. function:: on_message(message)

    Called when a :class:`Message` is created and sent.

    .. warning::

        Your bot's own messages and private messages are sent through this
        event. This can lead cases of 'recursion' depending on how your bot was
        programmed. If you want the bot to not reply to itself, consider
        checking the user IDs.

    :param message: The current message.
    :type message: :class:`Message`

.. function:: on_message_delete(message)

    Called when a message is deleted. If the message is not found in the
    internal message cache, then this event will not be called.
    Messages might not be in cache if the message is too old
    or the client is participating in high traffic servers.

    If this occurs increase the :class:`max_messages <Client>` parameter
    or use the :func:`on_raw_message_delete` event instead.

    :param message: The deleted message.
    :type message: :class:`Message`

.. function:: on_raw_message_delete(payload)

    Called when a message is deleted. Unlike :func:`on_message_delete`, this is
    called regardless of the message being in the internal message cache or not.

    If the message is found in the message cache,
    it can be accessed via :attr:`RawMessageDeleteEvent.cached_message`

    :param payload: The raw event payload data.
    :type payload: :class:`RawMessageDeleteEvent`

.. function:: on_message_edit(before, after)

    Called when a :class:`Message` receives an update event. If the message is not found
    in the internal message cache, then these events will not be called.
    Messages might not be in cache if the message is too old
    or the client is participating in high traffic servers.

    If this occurs increase the :class:`max_messages <Client>` parameter
    or use the :func:`on_raw_message_edit` event instead.

    The following non-exhaustive cases trigger this event:

    - The message content has been changed.

    :param before: The previous version of the message.
    :type before: :class:`Message`
    :param after: The current version of the message.
    :type after: :class:`Message`

.. function:: on_raw_message_edit(payload)

    Called when a message is edited. Unlike :func:`on_message_edit`, this is called
    regardless of the state of the internal message cache.

    If the message is found in the message cache,
    it can be accessed via :attr:`RawMessageUpdateEvent.cached_message`. The cached message represents
    the message before it has been edited. For example, if the content of a message is modified and
    triggers the :func:`on_raw_message_edit` coroutine, the :attr:`RawMessageUpdateEvent.cached_message`
    will return a :class:`Message` object that represents the message before the content was modified.

    :param payload: The raw event payload data.
    :type payload: :class:`RawMessageUpdateEvent`

.. function:: on_private_channel_delete(channel)
              on_private_channel_create(channel)

    Called whenever a private channel is deleted or created.

    :param channel: The private channel that got created or deleted.
    :type channel: :class:`abc.PrivateChannel`

.. function:: on_private_channel_update(before, after)

    Called whenever a private group DM is updated. e.g. changed name or topic.

    :param before: The updated group channel's old info.
    :type before: :class:`GroupChannel`
    :param after: The updated group channel's new info.
    :type after: :class:`GroupChannel`

.. function:: on_server_channel_delete(channel)
              on_server_channel_create(channel)

    Called whenever a server channel is deleted or created.

    Note that you can get the server from :attr:`~abc.ServerChannel.server`.

    :param channel: The guild channel that got created or deleted.
    :type channel: :class:`abc.ServerChannel`

.. function:: on_server_channel_update(before, after)

    Called whenever a server channel is updated. e.g. changed name, topic, permissions.

    :param before: The updated server channel's old info.
    :type before: :class:`abc.ServerChannel`
    :param after: The updated guild channel's new info.
    :type after: :class:`abc.ServerChannel`

.. function:: on_member_join(member)
              on_member_remove(member)

    Called when a :class:`Member` leaves or joins a :class:`Server`.

    This requires :attr:`Intents.members` to be enabled.

    :param member: The member who joined or left.
    :type member: :class:`Member`

.. function:: on_member_update(before, after)

    Called when a :class:`Member` updates their profile.

    This is called when one or more of the following things change:

    - status
    - nickname
    - roles

    :param before: The updated member's old info.
    :type before: :class:`Member`
    :param after: The updated member's updated info.
    :type after: :class:`Member`

.. function:: on_user_update(before, after)

    Called when a :class:`User` updates their profile.

    This is called when one or more of the following things change:

    - avatar
    - username

    :param before: The updated user's old info.
    :type before: :class:`User`
    :param after: The updated user's updated info.
    :type after: :class:`User`

.. function:: on_server_join(server)

    Called when a :class:`Server` is either created by the :class:`Client` or when the
    :class:`Client` joins a server.

    :param server: The server that was joined.
    :type server: :class:`Server`

.. function:: on_server_remove(server)

    Called when a :class:`Server` is removed from the :class:`Server`.

    This happens through, but not limited to, these circumstances:

    - The client got banned.
    - The client got kicked.
    - The client left the server.
    - The client or the server owner deleted the server.

    In order for this event to be invoked then the :class:`Server` must have
    been part of the server to begin with. (i.e. it is part of :attr:`Client.servers`)

    :param server: The server that got removed.
    :type server: :class:`Server`

.. function:: on_server_update(before, after)

    Called when a :class:`Server` updates, for example:

    - Changed name
    - etc

    :param before: The server prior to being updated.
    :type before: :class:`Server`
    :param after: The server after being updated.
    :type after: :class:`Server`

.. function:: on_server_role_create(role)
              on_server_role_delete(role)

    Called when a :class:`Server` creates or deletes a new :class:`Role`.

    To get the server it belongs to, use :attr:`Role.server`.

    :param role: The role that was created or deleted.
    :type role: :class:`Role`

.. function:: on_server_role_update(before, after)

    Called when a :class:`Role` is changed server-wide.

    :param before: The updated role's old info.
    :type before: :class:`Role`
    :param after: The updated role's updated info.
    :type after: :class:`Role`

.. function:: on_member_ban(server, user)

    Called when user gets banned from a :class:`Server`.

    :param server: The server the user got banned from.
    :type server: :class:`Server`
    :param user: The user that got banned.
                 Can be either :class:`User` or :class:`Member` depending if
                 the user was in the server or not at the time of removal.
    :type user: Union[:class:`User`, :class:`Member`]

.. function:: on_member_unban(server, user)

    Called when a :class:`User` gets unbanned from a :class:`Server`.

    :param server: The server the user got unbanned from.
    :type server: :class:`Server`
    :param user: The user that got unbanned.
    :type user: :class:`User`

.. function:: on_group_join(channel, user)
              on_group_remove(channel, user)

    Called when someone joins or leaves a :class:`GroupChannel`.

    :param channel: The group that the user joined or left.
    :type channel: :class:`GroupChannel`
    :param user: The user that joined or left.
    :type user: :class:`User`

.. function:: on_relationship_add(relationship)
              on_relationship_remove(relationship)

    Called when a :class:`Relationship` is added or removed from the
    :class:`ClientUser`.

    :param relationship: The relationship that was added or removed.
    :type relationship: :class:`Relationship`

.. function:: on_relationship_update(before, after)

    Called when a :class:`Relationship` is updated, e.g. when you
    block a friend or a friendship is accepted.

    :param before: The previous relationship status.
    :type before: :class:`Relationship`
    :param after: The updated relationship status.
    :type after: :class:`Relationship`

.. _defectio-api-utils:

Utility Functions
-----------------

.. autofunction:: defectio.utils.find

Async Iterator
----------------

Some API functions return an "async iterator". An async iterator is something that is
capable of being used in an :ref:`async for statement <py:async for>`.

These async iterators can be used as follows: ::

    async for elem in channel.history():
        # do stuff with elem here

Certain utilities make working with async iterators easier, detailed below.

.. class:: AsyncIterator

    Represents the "AsyncIterator" concept. Note that no such class exists,
    it is purely abstract.

    .. container:: operations

        .. describe:: async for x in y

            Iterates over the contents of the async iterator.


    .. method:: next()
        :async:

        |coro|

        Advances the iterator by one, if possible. If no more items are found
        then this raises :exc:`NoMoreItems`.

    .. method:: get(**attrs)
        :async:

        |coro|

        Similar to :func:`utils.get` except run over the async iterator.

        Getting the last message by a user named 'Dave' or ``None``: ::

            msg = await channel.history().get(author__name='Dave')

    .. method:: find(predicate)
        :async:

        |coro|

        Similar to :func:`utils.find` except run over the async iterator.

        Unlike :func:`utils.find`\, the predicate provided can be a
        |coroutine_link|_.

        Getting the last audit log with a reason or ``None``: ::

            def predicate(event):
                return event.reason is not None

            event = await guild.audit_logs().find(predicate)

        :param predicate: The predicate to use. Could be a |coroutine_link|_.
        :return: The first element that returns ``True`` for the predicate or ``None``.

    .. method:: flatten()
        :async:

        |coro|

        Flattens the async iterator into a :class:`list` with all the elements.

        :return: A list of every element in the async iterator.
        :rtype: list

    .. method:: chunk(max_size)

        Collects items into chunks of up to a given maximum size.
        Another :class:`AsyncIterator` is returned which collects items into
        :class:`list`\s of a given size. The maximum chunk size must be a positive integer.

        .. versionadded:: 1.6

        Collecting groups of users: ::

            async for leader, *users in reaction.users().chunk(3):
                ...

        .. warning::

            The last chunk collected may not be as large as ``max_size``.

        :param max_size: The size of individual chunks.
        :rtype: :class:`AsyncIterator`

    .. method:: map(func)

        This is similar to the built-in :func:`map <py:map>` function. Another
        :class:`AsyncIterator` is returned that executes the function on
        every element it is iterating over. This function can either be a
        regular function or a |coroutine_link|_.

        Creating a content iterator: ::

            def transform(message):
                return message.content

            async for content in channel.history().map(transform):
                message_length = len(content)

        :param func: The function to call on every element. Could be a |coroutine_link|_.
        :rtype: :class:`AsyncIterator`

    .. method:: filter(predicate)

        This is similar to the built-in :func:`filter <py:filter>` function. Another
        :class:`AsyncIterator` is returned that filters over the original
        async iterator. This predicate can be a regular function or a |coroutine_link|_.

        Getting messages by non-bot accounts: ::

            def predicate(message):
                return not message.author.bot

            async for elem in channel.history().filter(predicate):
                ...

        :param predicate: The predicate to call on every element. Could be a |coroutine_link|_.
        :rtype: :class:`AsyncIterator`

Defectio Models
---------------

Models are classes that are received from Revolt and are not meant to be created by
the user of the library.

.. danger::

    The classes listed below are **not intended to be created by users** and are also
    **read-only**.

    For example, this means that you should not make your own :class:`User` instances
    nor should you modify the :class:`User` instance yourself.

    If you want to get one of these model classes instances they'd have to be through
    the cache, and a common way of doing so is through the :func:`utils.find` function
    or attributes of model classes that you receive from the events specified in the
    :ref:`defectio-api-events`.

.. note::

    Nearly all classes here have :ref:`py:slots` defined which means that it is
    impossible to have dynamic attributes to the data classes.

User
~~~~~

.. attributetable:: User

.. autoclass:: User()
    :members:
    :inherited-members:

Message
~~~~~~~

.. attributetable:: Message

.. autoclass:: Message()
    :members:

Server
~~~~~~

.. attributetable:: Server

.. autoclass:: Server()
    :members:

Member
~~~~~~

.. attributetable:: Member

.. autoclass:: Member()
    :members:
    :inherited-members:

Role
~~~~~

.. attributetable:: Role

.. autoclass:: Role()
    :members:

TextChannel
~~~~~~~~~~~~

.. attributetable:: TextChannel

.. autoclass:: TextChannel()
    :members:
    :inherited-members:

DMChannel
~~~~~~~~~

.. attributetable:: DMChannel

.. autoclass:: DMChannel()
    :members:
    :inherited-members:

GroupChannel
~~~~~~~~~~~~

.. attributetable:: GroupChannel

.. autoclass:: GroupChannel()
    :members:
    :inherited-members:

RawMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawMessageDeleteEvent

.. autoclass:: RawMessageDeleteEvent()
    :members:

RawMessageUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawMessageUpdateEvent

.. autoclass:: RawMessageUpdateEvent()
    :members:
