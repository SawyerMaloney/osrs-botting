import cv2
import numpy as np
import mss
import time
from pynput import mouse, keyboard
import sys
import json
import random

class RubyMaker:
    def __init__(self):
        self.count = 0
        self.steps = ["get gold", "get diamonds"]
        self.locations = {}
        self.mouse_ctrl = mouse.Controller()
        self.keyboard = keyboard.Controller()

        # Remember, BGR
        self.furnace_color = np.array([0, 255, 0])
        self.open_bank_color = np.array([0, 0, 255])
        self.inv_slot_color = np.array([255, 75, 125])

        tolerance = 5

        self.furnace_color_lower = np.clip(self.furnace_color - tolerance, 0, 255)
        self.furnace_color_upper = np.clip(self.furnace_color + tolerance, 0, 255)
        self.open_bank_color_lower = np.clip(self.open_bank_color - tolerance, 0, 255)
        self.open_bank_color_upper = np.clip(self.open_bank_color + tolerance, 0, 255)
        self.inv_slot_color_lower = np.clip(self.inv_slot_color - tolerance, 0, 255)
        self.inv_slot_color_upper = np.clip(self.inv_slot_color + tolerance, 0, 255)

        self.MIN_AREA = 10

        self.gold_template = cv2.imread("gold.png", cv2.IMREAD_UNCHANGED)
        self.gold_template = cv2.cvtColor(self.gold_template, cv2.COLOR_BGRA2BGR)
        self.diamond_template = cv2.imread("ruby.png", cv2.IMREAD_UNCHANGED)
        self.diamond_template = cv2.cvtColor(self.diamond_template, cv2.COLOR_BGRA2BGR)
        self.furnace_screen_template = cv2.imread("furnace_screen.png", cv2.IMREAD_UNCHANGED)
        self.furnace_screen_template = cv2.cvtColor(self.furnace_screen_template, cv2.COLOR_BGRA2BGR)
        self.bank_icon_template = cv2.imread("bank_icon.png", cv2.IMREAD_UNCHANGED)
        self.bank_icon_template = cv2.cvtColor(self.bank_icon_template, cv2.COLOR_BGRA2BGR)
        
    def left_click(self):
        self.mouse_ctrl.click(mouse.Button.left, 1)

    def move_mouse(self, loc):
        self.mouse_ctrl.position = loc

    def setup_locations(self, key):
        if key == keyboard.Key.space:
            pos = self.mouse_ctrl.position
            print(f"adding {pos} for {self.steps[self.count]}")
            self.locations[self.steps[self.count]] = pos
            self.count += 1
            if self.count == len(self.steps):
                return False
            print(f"next, {self.steps[self.count]}")
        return True
    
    def block_on_go_to_image(self, sct, template, move=True, click=True):
        img, max_val = self.go_to_image(sct, template, move=move, click=click)
        while not img:
            img, max_val = self.go_to_image(sct, template, move=move, click=click)
        return img, max_val
    
    def bot(self, key):
        """
            Central botting function
            
            Assuming--  zoomed out, looking north, camera tilted up
                        full inventory (13/13), sprint OFF to start
        """
        default_wait = .5
        if key == keyboard.Key.space:
            with mss.mss() as sct:
                while True:
                    print("Moving to furnace...")
                    self.go_to_color(sct, self.furnace_color_lower, self.furnace_color_upper)
                    # block on not seeing furnace screen
                    print("Blocking on furnace screen template")
                    self.block_on_go_to_image(sct, self.furnace_screen_template, click=False)
                    self.wait(default_wait)
                    print("Pressing space...")
                    self.keyboard.press(keyboard.Key.space)
                    time.sleep(25)  # furnace smelting time
                    print("opening bank...")
                    self.go_to_color(sct, self.open_bank_color_lower, self.open_bank_color_upper)
                    self.block_on_go_to_image(sct, self.bank_icon_template, click=False)
                    print("depositing...")
                    self.go_to_color(sct, self.inv_slot_color_lower, self.inv_slot_color_upper)
                    self.wait(default_wait)
                    print("grabbing gold and diamonds...")
                    self.move_mouse(self.locations["get gold"])
                    self.wait(default_wait)
                    self.left_click()
                    self.wait(default_wait)
                    self.move_mouse(self.locations["get diamonds"])
                    self.wait(default_wait)
                    self.left_click()
                    self.wait(default_wait)
                    
                    # randomly wait for three minutes for realness
                    if random.randint(1, 10) == 10:
                        print("sleeping for three minutes...")
                        time.sleep(180)  
                return False

    def wait(self, default_wait):
        time.sleep(default_wait + random.random())

    def go_to_image(self, sct, image, threshold=.8, move=True, click=True):
        monitor = sct.monitors[0]
        screenshot = np.array(sct.grab(monitor))
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:
            t_height, t_width = template_gray.shape[:2]
            center_x = max_loc[0] + t_width // 2
            center_y = max_loc[1] + t_height // 2
            if move:
                print(f"moving to {center_x}, {center_y}")
                self.move_mouse((center_x, center_y))
                time.sleep(.3)
            if click:
                print("Clicking...")
                self.left_click()
                time.sleep(.3)
            return True, max_val
        else:
            return False, max_val # no good match

    def go_to_color(self, sct, color_lower, color_upper):
        monitor = sct.monitors[0]
        screenshot = np.array(sct.grab(monitor))
        screen = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        mask = cv2.inRange(screen, color_lower, color_upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"found {len(contours)} contours.")
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.MIN_AREA:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            cx = x + w // 2
            cy = y + h // 2
            print(f"moving mouse to {cx}, {cy} and clicking!")
            self.move_mouse((cx, cy))
            time.sleep(.3)
            self.left_click()
            time.sleep(.3)
            return 0
            

    def run(self):
        # load_config = input("Do you want to load the previous config? (y/n): ")
        # --------- override --------- #
        load_config = 'y'
        if load_config == 'y':
            print("Loading previous config...")
            with open("ruby_config.json", "r") as f:
                self.locations = json.load(f)
        else:
            print('gold, diamond')
            with keyboard.Listener(on_press=self.setup_locations) as listener:
                listener.join()

            print(self.locations)
            print("dumping config...")
            with open("ruby_config.json", "w") as f:
                json.dump(self.locations, f)

        print("Press space when you're ready to start the bot.")
        with keyboard.Listener(on_press=self.bot) as listener:
            listener.join()

bot = RubyMaker()
bot.run()

"""
running to bank -- 10 seconds
smelting -- 25 seconds
running back to bank -- 5.24

bank color -- 255, 0, 255
furnace color -- 255, 0, 0
"""