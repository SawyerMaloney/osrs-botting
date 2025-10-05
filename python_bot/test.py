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
            print("checking inv slot 1, 0")
            self.check_inv_slot(1, 0)
            print("checking inv slot 1, 1")
            self.check_inv_slot(1, 1)
            return False
    
bot = Test()
bot.bot()