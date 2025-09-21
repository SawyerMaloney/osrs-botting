import cv2
import numpy as np
import mss
import time
from pynput import mouse, keyboard
import sys
import json
import random
from datetime import datetime

class HighAlch:
    def __init__(self):
        self.mouse_ctrl = mouse.Controller()
        self.keyboard = keyboard.Controller()

        self.count = 0
        self.item_locs = []
        self.magic_tab_loc = (0, 0)

        self.high_alch_template = cv2.imread("high_alch.png", cv2.IMREAD_UNCHANGED)
        self.high_alch_template = cv2.cvtColor(self.high_alch_template, cv2.COLOR_BGRA2BGR)

        self.high_alch_loc = (0, 0, 0, 0)

    def left_click(self):
        self.mouse_ctrl.click(mouse.Button.left, 1)

    def move_mouse(self, loc):
        self.mouse_ctrl.position = loc

    def wait(self, default_wait=.5):
        time.sleep(default_wait + random.random())

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
                        img = self.go_to_image(sct, self.high_alch_template)
                        while not img:
                            img = self.go_to_image(sct, self.high_alch_template)
                        print(f"moving mouse to {self.item_locs[item]}")
                        self.move_mouse(self.item_locs[item])
                        self.wait(default_wait)
                        self.left_click()
                        self.move_mouse(self.magic_tab_loc)
                        # randomly wait for three minutes for realness
                        if random.randint(1, 100) == 50:
                            print("sleeping for three minutes...")
                            time.sleep(180) 

            return False
        return True

    def go_to_image(self, sct, image, threshold=.8):
        if self.high_alch_loc == (0, 0, 0, 0):
            monitor = sct.monitors[0]
            screenshot = np.array(sct.grab(monitor))
        else:
            region = {
                "left": self.high_alch_loc[0], 
                "top": self.high_alch_loc[1], 
                "height": self.high_alch_loc[2] + 50, 
                "width": self.high_alch_loc[3] + 50
                }
            screenshot = np.array(sct.grab(region))
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        template_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:
            t_height, t_width = template_gray.shape[:2]
            center_x = max_loc[0] + t_width // 2
            center_y = max_loc[1] + t_height // 2
            if self.high_alch_loc == (0, 0, 0, 0):
                self.high_alch_loc = (max_loc[0], max_loc[1], t_height, t_width)
            else:
                # convert to global screenspace
                center_x += self.high_alch_loc[0]
                center_y += self.high_alch_loc[1]
            print(f"moving to {center_x}, {center_y} and clicking")
            self.move_mouse((center_x, center_y))
            self.wait()
            self.left_click()
            self.wait
            
            return True
        else:
            return False # no good match

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

if __name__ == "__main__":
    bot = HighAlch()
    bot.run()

"""
    alching takes ~3 seconds
"""