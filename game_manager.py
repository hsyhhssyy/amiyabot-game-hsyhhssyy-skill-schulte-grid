import datetime

class GameManager:
    def __init__(self, max_time, callback=None):
        self.max_time = max_time
        self.callback = callback
        self.start_time = datetime.datetime.now()
        self.last_talk_time = self.start_time

    async def start(self, data, ask=None):

        while True:
            event = await data.wait_channel(ask, force=True, clean=bool(ask), max_time=5)
            
            try:
                ask = None # Only ask the first time

                current_time = datetime.datetime.now()

                elapsed_time = (current_time - self.start_time).seconds
                time_since_last_talk = (current_time - self.last_talk_time).seconds

                if event:
                    self.last_talk_time = current_time

                if elapsed_time > self.max_time:
                    return None

                if self.callback:
                    result = await self.callback(event, elapsed_time, time_since_last_talk)
                    if result is None:  # If callback returns None, break the loop
                        return
                                    
            finally:
                if event:
                    event.close_event()