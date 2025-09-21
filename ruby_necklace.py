import cv2
import numpy as np
import mss
import time
from pynput import mouse, keyboard
import sys
import json

class RubyMaker:
    def __init__(self):
        self.count = 0
        self.steps = ["go to furnace", "open furnace", "make necklace", "toggle sprint", "go to bank", "open bank", "deposit", "withdraw ruby", "withdraw gold", "close"]
        self.locations = {}
        self.mouse_ctrl = mouse.Controller()
        self.keyboard = keyboard.Controller()

        # Remember, BGR
        self.bank_color = np.array([0, 255, 0])
        self.furnace_tile_color = np.array([0, 0, 255])
        self.furnace_color = np.array([255, 0, 0])
        self.open_bank_color = np.array([255, 255, 0])
        self.inv_slot_color = np.array([255, 75, 125])

        tolerance = 5

        self.bank_color_lower = np.clip(self.bank_color - tolerance, 0, 255)
        self.bank_color_upper = np.clip(self.bank_color + tolerance, 0, 255)
        self.furnace_tile_color_lower = np.clip(self.furnace_tile_color - tolerance, 0, 255)
        self.furnace_tile_color_upper = np.clip(self.furnace_tile_color + tolerance, 0, 255)
        self.furnace_color_lower = np.clip(self.furnace_color - tolerance, 0, 255)
        self.furnace_color_upper = np.clip(self.furnace_color + tolerance, 0, 255)
        self.open_bank_color_lower = np.clip(self.open_bank_color - tolerance, 0, 255)
        self.open_bank_color_upper = np.clip(self.open_bank_color + tolerance, 0, 255)
        self.inv_slot_color_lower = np.clip(self.inv_slot_color - tolerance, 0, 255)
        self.inv_slot_color_upper = np.clip(self.inv_slot_color + tolerance, 0, 255)

        self.MIN_AREA = 10

        self.gold_template = cv2.imread("gold.png", cv2.IMREAD_UNCHANGED)
        self.gold_template = cv2.cvtColor(self.gold_template, cv2.COLOR_BGRA2BGR)
        self.ruby_template = cv2.imread("ruby.png", cv2.IMREAD_UNCHANGED)
        self.ruby_template = cv2.cvtColor(self.ruby_template, cv2.COLOR_BGRA2BGR)
        
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
    
    def bot(self, key):
        """
            Central botting function
            
            Assuming--  zoomed out, looking north, camera tilted up
                        full inventory (13/13), sprint OFF to start
        """
        default_wait = .5
        if key == keyboard.Key.space:
            with mss.mss() as sct:
                for _ in range(8):
                    print("moving to furnace tile")
                    self.go_to_color(sct, self.furnace_tile_color_lower, self.furnace_tile_color_upper)
                    time.sleep(10)
                    print("interacting with furnace")
                    self.go_to_color(sct, self.furnace_color_lower, self.furnace_color_upper)
                    time.sleep(default_wait)
                    print("pressing space...")
                    self.keyboard.press(keyboard.Key.space)
                    time.sleep(25)
                    print("going to bank")
                    self.go_to_color(sct, self.bank_color_lower, self.bank_color_upper)
                    time.sleep(10)
                    print("opening bank...")
                    self.go_to_color(sct, self.open_bank_color_lower, self.open_bank_color_upper)
                    time.sleep(default_wait)
                    print("depositing...")
                    self.go_to_color(sct, self.inv_slot_color_lower, self.inv_slot_color_upper)
                    time.sleep(default_wait)
                    print("grabbing gold and rubies...")
                    self.go_to_image(sct, self.gold_template)
                    time.sleep(default_wait)
                    self.go_to_image(sct, self.ruby_template)
                return False


    def go_to_image(self, sct, image, threshold=.8):
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
            print(f"moving to {center_x}, {center_y} and clicking")
            self.move_mouse((center_x, center_y))
            time.sleep(.3)
            self.left_click()
            time.sleep(.3)            

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
                print(f"discarding contour with area {area}")
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
            print('"go to furnace", "open furance", "make necklace", "toggle sprint", "go to bank", "open bank", "deposit", "withdraw ruby", "withdraw gold", "close"')
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

                self.move_mouse(self.locations['go to furnace'])
                self.left_click()
                time.sleep(10)
                self.move_mouse(self.locations['open furnace'])
                time.sleep(default_wait)
                self.left_click()
                time.sleep(3)
                self.move_mouse(self.locations['make necklace'])
                self.left_click()
                time.sleep(25)
                self.move_mouse(self.locations['toggle sprint'])
                time.sleep(default_wait)
                self.left_click()
                time.sleep(default_wait)
                self.move_mouse(self.locations['go to bank'])
                time.sleep(default_wait)
                self.left_click()
                time.sleep(6)
                self.move_mouse(self.locations['open bank'])
                time.sleep(default_wait)
                self.left_click()
                time.sleep(default_wait)
                self.move_mouse(self.locations['deposit'])
                self.left_click()
                time.sleep(default_wait)
                self.move_mouse(self.locations['withdraw ruby'])
                self.left_click()
                time.sleep(default_wait)
                self.move_mouse(self.locations['withdraw gold'])
                self.left_click()
                self.move_mouse(self.locations['close'])
                self.left_click()
                time.sleep(default_wait)
                self.move_mouse(self.locations['toggle sprint'])
                self.left_click()


"""