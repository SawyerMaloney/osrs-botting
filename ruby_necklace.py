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
        default_wait = 1
        if key == keyboard.Key.space:
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
"""