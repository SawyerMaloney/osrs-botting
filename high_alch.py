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

        self.log_out_template = cv2.imread("log_out.png", cv2.IMREAD_UNCHANGED)
        self.log_out_template = cv2.cvtColor(self.log_out_template, cv2.COLOR_BGRA2BGR)

        self.log_out_button_template = cv2.imread("log_out_button.png", cv2.IMREAD_UNCHANGED)
        self.log_out_button_template = cv2.cvtColor(self.log_out_button_template, cv2.COLOR_BGRA2BGR)

        self.cached_region = None

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
                        img = self.go_to_image(sct, self.high_alch_template, True)
                        while not img:
                            img = self.go_to_image(sct, self.high_alch_template, True)
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

    def go_to_image(self, sct, image, caching, threshold=.8, debug=False):
        if not caching or self.cached_region == None:
            monitor = sct.monitors[0]
            screenshot = np.array(sct.grab(monitor))
        else:
            region = {
                "left": self.cached_region["left"], 
                "top": self.cached_region["top"], 
                "height": self.cached_region["height"] + 50, 
                "width": self.cached_region["width"] + 50
                }
            screenshot = np.array(sct.grab(region))
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        template_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if debug:
            # Draw rectangle around best match
            top_left = max_loc
            h, w = template_gray.shape[:2]
            bottom_right = (top_left[0] + w, top_left[1] + h)

            # Make a color copy for visualization
            screenshot_vis = cv2.cvtColor(screenshot_gray, cv2.COLOR_GRAY2BGR)
            cv2.rectangle(screenshot_vis, top_left, bottom_right, (0, 0, 255), 2)

            # Show the image
            cv2.imshow("Template Match", screenshot_vis)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        if max_val > threshold:
            t_height, t_width = template_gray.shape[:2]
            center_x = max_loc[0] + t_width // 2
            center_y = max_loc[1] + t_height // 2
            if caching and self.cached_region is not None:
                # convert to global screenspace
                center_x += self.cached_region["left"]
                center_y += self.cached_region["top"]
            elif caching:
                self.cached_region = {
                "left": max_loc[0],
                "top": max_loc[1],
                "height": t_height,
                "width": t_width
                }

            print(f"moving to {center_x}, {center_y} and clicking")
            self.move_mouse((center_x, center_y))
            self.wait()
            self.left_click()
            self.wait
           
            return True
        else:
            print(f"No good match. max_val: {max_val}")
            return False # no good match
        
    def log_out(self):
        with mss.mss() as sct:
            print("Going to logout screen...")
            self.go_to_image(sct, self.log_out_template, False)
            self.wait()
            print("Pressing log out...")
            img = self.go_to_image(sct, self.log_out_button_template, False, threshold=.5)  # bye bye!
            while not img:
                img = self.go_to_image(sct, self.log_out_button_template, False, threshold=.5)  # bye bye!
            print("Log out pressed.")
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