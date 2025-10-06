import cv2
import mss
import time
from pynput import mouse, keyboard
from datetime import datetime
from bot import Bot

class HighAlch(Bot):
    def __init__(self):
        super().__init__()  # Initialize the parent Bot class

        self.count = 0
        self.item_loc = (2, 0)
        self.magic_tab_loc = (0, 0)

        self.high_alch_template = cv2.imread(self.template_path("high_alch.png"), cv2.IMREAD_UNCHANGED)
        self.high_alch_template = cv2.cvtColor(self.high_alch_template, cv2.COLOR_BGRA2BGR)

    def on_press(self, key):
        if key == keyboard.Key.space:
            self.item_locs.append(self.mouse_ctrl.position)
            print(f"adding {self.mouse_ctrl.position} for item {self.count}")
            self.count += 1
            if self.count == len(self.stack_sizes):
                return False
            
        return True

    def bot(self, key):
        default_wait = .5
        if key == keyboard.Key.space:
            self.open_magic_tab()
            with mss.mss() as sct:
                for item in range(len(self.item_loc)):
                    while True:
                        # block until we see the high alch icon
                        self.block_on_go_to_image(sct, self.high_alch_template, True)
                        self.wait()
                        if not self.has_item(self.item_loc[0], self.item_loc[1], debug=True):
                            if self.item_loc[0] < 3:
                                self.item_loc = (self.item_loc[0] + 1, self.item_loc[1])
                            else:
                                print("moving down a row")
                                self.item_loc = (0, self.item_loc[1] + 1)
                                print(f"item_loc: {self.item_loc}")
                            if not self.has_item(self.item_loc[0], self.item_loc[1]):
                                print("Done with high alching.")
                                return False
                        print(f"in high_alch, using item_loc {self.item_loc}")
                        self.use_item(self.item_loc[0], self.item_loc[1])
                        self.wait()                        
                        self.reset_mouse()

            return False
        return True
        
    def run(self):
        print("Press space to run the automation.")
        with keyboard.Listener(on_press=self.bot) as listener:
            listener.join()

        print(f"High alching finished at {datetime.fromtimestamp(time.time())}.")
        self.wait(2)

if __name__ == "__main__":
    bot = HighAlch()
    bot.run()

"""
    alching takes ~3 seconds
"""