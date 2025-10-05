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
        self.item_locs = []
        self.magic_tab_loc = (0, 0)

        self.high_alch_template = cv2.imread(self.template_path("high_alch.png"), cv2.IMREAD_UNCHANGED)
        self.high_alch_template = cv2.cvtColor(self.high_alch_template, cv2.COLOR_BGRA2BGR)

    def on_press(self, key):
        if key == keyboard.Key.space:
            if self.count == len(self.stack_sizes):
                pos = self.mouse_ctrl.position
                self.magic_tab_loc = pos
                print(f"adding magic tab loc as {pos}")
                return False
            self.item_locs.append(self.mouse_ctrl.position)
            print(f"adding {self.mouse_ctrl.position} for item {self.count}")
            self.count += 1
            
        return True

    def bot(self, key):
        default_wait = .5
        if key == keyboard.Key.space:
            with mss.mss() as sct:
                for item in range(len(self.item_locs)):
                    for iter in range(self.stack_sizes[item]):
                        # block until we see the high alch icon
                        img = self.go_to_image(sct, self.high_alch_template, True)
                        while not img:
                            img = self.go_to_image(sct, self.high_alch_template, True)
                        print(f"moving mouse to {self.item_locs[item]}")
                        self.move_mouse(self.item_locs[item])
                        self.wait(default_wait)
                        self.left_click()
                        self.move_mouse(self.magic_tab_loc)
                        # # randomly wait for three minutes for realness
                        # if random.randint(1, 100) == 50:
                        #     print("sleeping for three minutes...")
                        #     time.sleep(180) 

            return False
        return True
        
    def run(self):
        num_items = int(input("how many items: "))
        self.stack_sizes = [0] * num_items
        for item in range(len(self.stack_sizes)):
            self.stack_sizes[item] = int(input(f"how many items in stack {item}: "))
        
        print("press space over each item")
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

        print(f"Item positions: {self.item_locs}")

        print("Press space to run the automation.")
        with keyboard.Listener(on_press=self.bot) as listener:
            listener.join()

        print(f"High alching finished at {datetime.fromtimestamp(time.time())}.")

        self.log_out()

if __name__ == "__main__":
    bot = HighAlch()
    bot.run()

"""
    alching takes ~3 seconds
"""