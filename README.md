# Background Tasks with Channels in Django


## Overview

This is a simple walkthrough of creating a very basic app that utilizes Channels for handling
background tasks.

Please feel free to contribute with error corrections, improvements, or demonstrations of additional
concepts relevant to Channels.


## Tutorial

### Step 1: Get dependencies in place

Set up a virtual environment with Python 3.6, setuptools, pip, and wheel. Then install Django and
Channels:

```shell
$> mkdir bgtasks-example && cd bgtasks-example

$> touch .envrc && echo "layout python3" > .envrc && direnv allow  # I'm using direnv for env. mgmt.

$> pip install django channels channels_redis
```
*This was written with Django==2.0.3 and Channels==2.0.2.*

You will also need a running redis server. Here is how that can be accomplished with Homebrew on
OSX:

```shell
$> brew update

$> brew install redis
...
==> Summary
🍺  /usr/local/Cellar/redis/4.0.8: 13 files, 2.8MB

$> brew services start redis

$> redis-cli ping
PONG
```
*The default binding address for redis is `bind 127.0.0.1 ::1` (i.e., listen at all addresses) and
the default port is `6379`.*


### Step 2: Initialize a blank Django project

```shell
$> django-admin startproject bgtasks .
```
*Don't forget the `.` if you're already in your project folder to tell Django not to create a new
folder.*


### Step 3: Start a new app for background tasks to call home

Create the new app:

```shell
$> python manage.py startapp tasks
```

And start a `consumers.py` file at `./tasks/consumers.py`:

**./tasks/consumers.py**
```python
from time import sleep
from channels.consumer import SyncConsumer

class BackgroundTaskConsumer(SyncConsumer):
    def task_a(self, message):
        sleep(5)

    def task_b(self, message):
        sleep(message['wait'])
```

We now have a consumer with two methods. `BackgroundTaskConsumer.task_a` will simply sleep for 5
seconds. `BackgroundTaskConsumer.task_b` will wait for the number of seconds passed via
`message['wait']`.


### Step 5: Set up channel routing

Create a new file called `routing.py` next to the stock `urls.py`:

**./bgtasks/routing.py**
```python
from channels.routing import ChannelNameRouter, ProtocolTypeRouter
from tasks.consumers import BackgroundTaskConsumer

application = ProtocolTypeRouter({
    'channel': ChannelNameRouter({
        'background-tasks': BackgroundTaskConsumer,
    })
})
```

We now have a channel routing that will send any messages in the `background-task` queue to our
`BackgroundTaskConsumer` that we created earlier. We'll see how these messages are directed to
`BackgroundTaskConsumer.task_a` and `BackgroundTaskConsumer.task_b` when we add messages to the
queue.


### Step 6: Integrate with Django

**./bgtasks/bgtasks/settings.py**
```python
# ...

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Add channels to INSTALLED_APPS
    'channels',
]

# ...

WSGI_APPLICATION = 'bgtasks.wsgi.application'

# Add a setting ASGI_APPLICATION to point at the application in routing.py
ASGI_APPLICATION = 'bgtasks.routing.application'

# ...

# Add a new CHANNEL_LAYERS setting that points to a redis instance
# According to the Channels docs, only the redis layer is updated to match Channels 2.
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLalyer',
        'CONFIG': {
            'hosts': [('localhost', 6379)]
        }
    }
}

# ...
```
*Be sure to update `CHANNEL_LAYERS` to point to your actual redis instance if needed*

We now have everything in place to run the application. If you boot up the development server,
you'll notice it looks similar to the typical server, but with some slight changes - most notably
there's talk of ASGI in the output:

```shell
$> python manage.py runserver
Django version 2.0.3, using settings 'bgtasks.settings'
Starting ASGI/Channels development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
2018-03-10 18:31:32,276 - INFO - server - HTTP/2 support not enabled (install the http2 and tls Twisted extras)
2018-03-10 18:31:32,277 - INFO - server - Configuring endpoint tcp:port=8000:interface=127.0.0.1
2018-03-10 18:31:32,278 - INFO - server - Listening on TCP address 127.0.0.1:8000
```


### Step 7: Create some views that make use of our background tasks

Create yet another app (yes, it's overkill here, but models the way your app may be structured in
reality) for some basic views to call home:

```shell
$> python manage.py startapp starttasks
```

And add some super-simple views:

**./starttasks/views.py**
```python
from random import randint
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse

channel_layer = get_channel_layer()

def start_task_a(request):
    id = randint(0,1000)
    async_to_sync(channel_layer.send)('background-tasks', {'type': 'task_a', 'id': id})
    return HttpResponse('task_a message sent with id={}'.format(id), content_type='text/plain')

def start_task_b(request, wait):
    async_to_sync(channel_layer.send)('background-tasks', {'type': 'task_b', 'wait': wait})
    return HttpResponse('task_b message sent with wait={}'.format(wait), content_type='text/plain')

```

And ensure the views are mapped in the `urls.py` file:

**./bgtasks/urls.py**
```python
from django.contrib import admin
from django.urls import path
from starttasks import views

urlpatterns = [
    path('start-task-a/', views.start_task_a),             # e.g., GET /start-task-a/
    path('start-task-b/<int:wait>/', views.start_task_b),  # e.g., GET /start-task-b/10/
    path('admin/', admin.site.urls),
]
```

Everything is now ready to go!!


### Step 8: Boot up the development server and a worker and see if it works

First, start up a worker for responding to web requests (`http`-typed channel messages):

```shell
$> python manage.py runserver
```

Next, in a separate terminal window, start up a worker that will wait for background tasks:

```shell
$> python manage.py runworker background-tasks
```
*You must explicitly list out the channels the worker should respond to.*

Now, if you open a browser and navigate to **http://localhost:8000/start-task-a/** you should see
a response like this:

```
task_a message sent with id=483
```

And you should be able to watch the task complete in your worker terminal:
```
BackgroundTaskConsumer.task_a started with message.id=483
BackgroundTaskConsumer.task_a completed with message.id=483
```

With only one worker, tasks will be taken first-come first serve and can back up quickly (try
submitting multiple requests to **http://localhost:8000/start-task-a/** very quickly then watch
the worker chomp through them one at a time).

You can boot up more workers in more terminal windows to clear the background task queue faster.

Because the server worker and the background task worker are separated, your server will stay
responsive even if the background task queue is backlogged.
