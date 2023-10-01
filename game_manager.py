import datetime

async def wait_generator(data, ask=None):

        start_time = datetime.datetime.now()
        last_talk_time = start_time

        while True:
            event = await data.wait_channel(ask, force=True, clean=bool(ask), max_time=5)
            
            try:
                ask = None # Only ask the first time

                current_time = datetime.datetime.now()

                elapsed_time = (current_time - start_time).seconds
                time_since_last_talk = (current_time - last_talk_time).seconds

                message = None
                if event:
                    last_talk_time = current_time
                    message=event.message

                yield message, elapsed_time, time_since_last_talk
                                    
            finally:
                if event:
                    event.close_event()

class GameManager:

    def __init__(self) -> None:
        self.gen = None

    async def wait(self,data,ask=None):
        try:
            if self.gen is None:
                self.gen = wait_generator(data, ask)
            return await self.gen.__anext__()
        except StopAsyncIteration:  # This exception is raised when the generator is exhausted
            return None, None, None