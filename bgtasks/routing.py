from channels.routing import ChannelNameRouter, ProtocolTypeRouter

from tasks.consumers import BackgroundTaskConsumer


application = ProtocolTypeRouter({
    # Messages with type `http` are handled with `urls.py` by default

    # Messages directed to a single channel will have a type `channel`
    'channel': ChannelNameRouter({
        # Messages directed to the `background-tasks` channel will be passed to our consumer
        'background-tasks': BackgroundTaskConsumer,
    })
})
