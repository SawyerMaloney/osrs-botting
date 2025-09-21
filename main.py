import cv2
import numpy as np
import mss
import time
from pynput import mouse, keyboard
import sys


class BananaMagic:
    def __init__(self):
        self.marking_count = 0
        #  banana cast, bank, bananas in inv, bones in bank, x
        self.steps = ["cast banana", "open bank", "put bananas in bank", "get more bones", "exit bank"]
        self.locations = []
        self.mouse_ctrl = mouse.Controller()
        self.running = True
        self.num_runs = 8
        self.keyboard = keyboard.Controller()
    
    def marking(self, key):
        if not self.running:
            return False
        if key == keyboard.Key.space:
            pos = self.mouse_ctrl.position
            print(f"adding step {self.steps[self.marking_count]}")
            self.locations.append((self.steps[self.marking_count], pos))   
            self.marking_count += 1
            print(f"incrementing marking count to {self.marking_count  }")
            if self.marking_count == len(self.steps  ):
                return False
            
        return True
        
    def left_click(self):
        self.mouse_ctrl.click(mouse.Button.left, 1)

    def move_mouse(self, loc):
        self.mouse_ctrl.position = loc
        
    def run_automation(self, key):
        if not self.running:
            return False
        if key == keyboard.Key.space:
            print(f"running automation... ({self.num_runs}x)")
            for i in range(self.num_runs):
                print(f"{i+1} execution...")
                for (step, pos) in self.locations:
                    if not self.running:
                        return False
                    print(f"executing step: {step}")
                    self.move_mouse(pos)
                    time.sleep(.3)
                    self.left_click()
                    time.sleep(.3)
            print("Done running automation.")
        
    def run(self):
        bones = input("How many bones do you need to convert: ")
        self.num_runs = bones / 26
        with keyboard.Listener(on_press=self.kill) as kill_listener:
            print("press space over: banana cast, bank, bananas in inv, bones in bank, bank x")
            with keyboard.Listener(on_press=self.marking) as listener:
                listener.join()

            print("automation set. press space again to run.")
            with keyboard.Listener(on_press=self.run_automation) as listener:
                listener.join()
            listener.join()

    def kill(self, key):
        if key == keyboard.KeyCode.from_char('q'):
            print("kill triggered")
            self.running = False
            return self.running



if __name__ == "__main__":
    banana_magic = BananaMagic()
    banana_magic.run()