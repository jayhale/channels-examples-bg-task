from time import sleep

from channels.consumer import SyncConsumer


class BackgroundTaskConsumer(SyncConsumer):

    def task_a(self, message):
        """Task A

        Expects a message with at least the `id` key and waits 5 seconds. E.g.:

        message = {'id': 1}                        # Valid
        message = {'id': 'string-id-woohoo!'}      # Valid
        message = {'other_key': 'some cool value'} # Not valid

        """
        if 'id' not in message.keys():
            raise ValueError('message must include an id key')

        print('BackgroundTaskConsumer.task_a started with message.id={}'.format(message['id']))
        sleep(5)
        print('BackgroundTaskConsumer.task_a completed with message.id={}'.format(message['id']))


    def task_b(self, message):
        """Task B

        Expectes a message with at least the `wait` key and waits for the associated value. E.g.:

        message = {'wait': 5}                      # Valid
        message = {'wait': 10}                     # Valid
        message = {'other_key': 'some cool value'} # Not valid

        """
        if 'wait' not in message.keys():
            raise ValueError('message must include a wait key')

        if not isinstance(message['wait'], int):
            raise ValueError('message[\'wait\'] must be an integer')

        print('BackgroundTaskConsumer.task_b started with message.wait={}'.format(message['wait']))
        sleep(message['wait'])
        print('BackgroundTaskConsumer.task_b completed with message.wait={}'.format(
            message['wait']))
