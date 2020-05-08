from typing import List

import toplevel.conf as conf
from dysart.hooks.hooks import pre_hook, post_hook
from dysart.feature import CallRecord
import dysart.messages.messages as messages

import aiohttp
from slack import WebClient
from slack.errors import SlackApiError

client = WebClient(token=conf.config['slack_api_token'],
                   run_async=True)


def to_channel(channel: str):
    @post_hook
    async def hook(record: CallRecord):
        with messages.FormatContext('slack'):
            text = record_message(record)
        try:
            response = await client.chat_postMessage(
                channel=channel,
                text=text
            )
        except SlackApiError as e:
            # TODO handle with a standard error message from messages module
            print(e)
        # This should trigger when the client wasn't created successfully
        except NameError:
            pass

    return hook


def to_users(*users: List[str]):
    try:
        # precompute the channel id to message these users
        response = client.conversations_open(users=users)
        channel_id = response["channel"]["id"]

        @post_hook
        async def hook(record: CallRecord):
            with messages.FormatContext('slack'):
                text = record_message(record)
            try:
                response = await client.chat_postMessage(
                    channel=channel_id,
                    text=text
                )
            except SlackApiError as e:
                # TODO handle with a standard error message from messages module
                print(e)
            # This should trigger when the client wasn't created successfully
            except NameError:
                pass
    except (SlackApiError, aiohttp.client_exceptions.ClientConnectorError) as e:
        # TODO handle with a standard error message from messages module
        print(e)

        # use a no-op hook
        @post_hook
        def hook(record: CallRecord):
            pass

    return hook

def record_message(record: CallRecord) -> str:
    return f"""A user has just completed a measurement or query,
    resulting in the following call record:

    {record}
    """
