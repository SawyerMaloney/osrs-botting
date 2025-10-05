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
            for h in range(2):
                 for w in range(4):
                      print(f"checking item {w}, {h}")
                      self.check_inv_slot(w, h)

            return False
    
bot = Test()
bot.bot()