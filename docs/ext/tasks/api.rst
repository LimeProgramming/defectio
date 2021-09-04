.. _ext_tasks_api:

API Reference
---------------

.. attributetable:: defectio.ext.tasks.Loop

.. autoclass:: defectio.ext.tasks.Loop()
    :members:
    :special-members: __call__
    :exclude-members: after_loop, before_loop, error

    .. automethod:: Loop.after_loop()
        :decorator:

    .. automethod:: Loop.before_loop()
        :decorator:

    .. automethod:: Loop.error()
        :decorator:

.. autofunction:: defectio.ext.tasks.loop
