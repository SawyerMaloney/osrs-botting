from bot import Bot
from pynput import keyboard

class Test(Bot):
    def __init__(self):
        super().__init__()
    
    def bot(self):
        print("waiting for space...")
        with keyboard.Listener(on_press=self.on_press) as listener:
                listener.join()
        print("End of bot execution.")

    def on_press(self, key):
         if key == keyboard.Key.space:
            print("using item 1,0")
            self.use_item(3, 0)
            self.wait(2)
            self.use_item(0, 1)
            return False
    
bot = Test()
bot.bot()