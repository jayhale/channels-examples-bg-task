from random import randint

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse


channel_layer = get_channel_layer()


# GET /start-task-a/
def start_task_a(request):
    """Enqueues a message on the `background-tasks` channel with type `task_a`"""

    # Generate a random id number for the message
    id = randint(0,1000)

    # Send our message to the queue
    async_to_sync(channel_layer.send)('background-tasks', {'type': 'task_a', 'id': id})

    # Let the user know we did something
    return HttpResponse('task_a message sent with id={}'.format(id), content_type='text/plain')


# GET /start-task-b/5/
def start_task_b(request, wait):
    """Enqueues a message om the `background-tasks` channel with type `task_b`"""

    # Send our message to the queue
    async_to_sync(channel_layer.send)('background-tasks', {'type': 'task_b', 'wait': wait})

    # Let the user know we did something
    return HttpResponse('task_b message sent with wait={}'.format(wait), content_type='text/plain')
