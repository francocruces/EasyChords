"""
Simple telegram inline bot with an inline keyboard. Gets lyrics from AZ Lyrics.
"""

import asyncio

import telepot
from telepot.aio.delegate import per_inline_from_id, create_open, pave_event_space, intercept_callback_query_origin
from telepot.aio.helper import InlineUserHandler, AnswererMixin, InterceptCallbackQueryMixin
from telepot.aio.loop import MessageLoop

from Config import MAX_MESSAGE_SIZE, MESSAGE_TOO_LONG_ALERT, CANCEL_DATA_STRING, SEARCH_CANCELLED_ALERT, TO_MONO
from Scraper import get_chords_as_inline_keyboard, get_chords
from __TOKEN__ import TOKEN  # Replace with your own token. Provided by BotFather

__author__ = "Franco Cruces Ayala"


class InlineHandler(InlineUserHandler, AnswererMixin, InterceptCallbackQueryMixin):
    """
    Handler for the inline bot.
    """

    def __init__(self, *args, **kwargs):
        super(InlineHandler, self).__init__(*args, **kwargs)

    async def on_inline_query(self, msg):
        """
        How to handle an inline query.
        :param msg: Telegram message. It's expected to be an inline_query
        :return: Results for the inline query
        """

        def compute_answer():
            """
            Function generating the answer for the handler.
            :return: Lyrics as articles
            """
            print(msg)
            return get_chords_as_inline_keyboard(msg['query'])

        self.answerer.answer(msg, compute_answer)

    def on_chosen_inline_result(self, msg):
        """
        Console printing for debugging.
        :param msg: Telegram message. It's expected to be a chosen_inline_result
        """
        print(msg)
        # TODO: Store for impact measuring

    async def on_callback_query(self, msg):
        print(msg)
        in_id = msg['inline_message_id']
        data = msg['data']
        if data == CANCEL_DATA_STRING:
            await self.bot.editMessageText(str(in_id), SEARCH_CANCELLED_ALERT, parse_mode="Markdown")
        else:
            lyrics = get_chords(data)
            if len(lyrics) <= MAX_MESSAGE_SIZE:
                await self.bot.editMessageText(str(in_id), TO_MONO + lyrics + TO_MONO, parse_mode="Markdown")
            else:
                await self.bot.editMessageText(str(in_id), MESSAGE_TOO_LONG_ALERT, parse_mode="Markdown")
                while lyrics != "":
                    await self.bot.sendMessage(msg['from']['id'], TO_MONO + lyrics[:MAX_MESSAGE_SIZE] + TO_MONO,
                                               parse_mode="Markdown")
                    lyrics = lyrics[MAX_MESSAGE_SIZE:]


# ASYNC MAIN
bot = telepot.aio.DelegatorBot(TOKEN, [intercept_callback_query_origin(
    pave_event_space())(
    per_inline_from_id(), create_open, InlineHandler, timeout=10)
])

loop = asyncio.get_event_loop()

loop.create_task(MessageLoop(bot).run_forever())
print('Listening ...')

loop.run_forever()
