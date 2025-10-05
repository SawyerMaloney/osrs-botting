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
            print("running, opening magic tab...")
            self.open_magic_tab()
            print("waiting 2 seconds...")
            self.wait(2)
            print("opening inventory tab...")
            self.open_inventory_tab()
            print("waiting 2 seconds...")
            self.wait(2)
            print("resetting mouse...")
            self.reset_mouse()
            self.wait(2)
            print("Logging out...")
            self.log_out()
            return False

bot = Test()
bot.bot()