import cv2
import numpy as np
import mss
import time
from pynput import mouse, keyboard
import json
import random


class BananaMagic:
    def __init__(self):
        self.marking_count = 0
        #  banana cast, bank, bananas in inv, bones in bank, x
        self.steps = ["cast banana", "open bank", "put bananas in bank", "get more bones", "exit bank"]
        self.locations = {}
        self.mouse_ctrl = mouse.Controller()
        self.running = True
        self.num_runs = 8
        self.keyboard = keyboard.Controller()

        self.bones_template = cv2.imread("bones.png", cv2.IMREAD_UNCHANGED)
        self.bones_template = cv2.cvtColor(self.bones_template, cv2.COLOR_BGRA2BGR)
        if self.bones_template is None:
            raise FileNotFoundError("bones.png not found")
        print(f"template shape: ", self.bones_template.shape)
        print(f"template dtype: ", self.bones_template.dtype)
    
    def marking(self, key):
        if not self.running:
            return False
        if key == keyboard.Key.space:
            pos = self.mouse_ctrl.position
            print(f"adding step {self.steps[self.marking_count]}")
            self.locations[self.steps[self.marking_count]] = pos  
            self.marking_count += 1
            print(f"incrementing marking count to {self.marking_count  }")
            if self.marking_count == len(self.steps  ):
                return False
            
        return True
        
    def left_click(self):
        self.mouse_ctrl.click(mouse.Button.left, 1)

    def move_mouse(self, loc):
        self.mouse_ctrl.position = loc

    def check_bones(self, sct):
        """
            check if we still have bones
            returns if bones are present (bool)
        """
        bones = False
        time.sleep(.5)

        screenshot = sct.grab(sct.monitors[0])
        screen = np.array(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
        print(f"screen shape: ", screen.shape)
        print(f"screen dtype: ", screen.dtype)
        

        if screen.shape[2] == 4:
            screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
  
        # template matching
        result = cv2.matchTemplate(screen, self.bones_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        threshold = 0.8
        if max_val >= threshold:
            print(f"found at {max_loc} (top_left)")
            return True
        return False
    
    def wait(self, default_wait):
        time.sleep(default_wait + random.random())
        
    def run_automation(self, key):
        if not self.running:
            return False
        if key == keyboard.Key.space:
            with mss.mss() as sct:
                for _ in range(self.iters):
                    print(f"running automation... ({self.num_runs}x)")
                    while True and self.running:
                        for step in self.locations.keys():
                            if not self.running:
                                return False
                            print(f"executing step: {step}")
                            self.move_mouse(self.locations[step])
                            self.wait(1)
                            self.left_click()
                            self.wait(1)
            print("Done running automation.")

    def load_from_config(self):
        try:
            with open("config.json", "r") as f:
                self.locations = json.load(f)    
                return True
        except Exception as e:
            print("Failed to load smart config with error {e}.\nForcing normal configuration.")
            return False
        
    def run(self):
        with keyboard.Listener(on_press=self.kill) as kill_listener:
            smart_load = input("Do you want to load previous config? (y/n): ")
            if smart_load == 'y':
                result = self.load_from_config()
            if (smart_load == 'y' and not result) or smart_load == 'n':
                print("press space over: banana cast, bank, bananas in inv, bones in bank, bank x")
                with keyboard.Listener(on_press=self.marking) as listener:
                    listener.join()
                print("dumping config...")
                with open("config.json", "w") as f:
                    json.dump(self.locations, f)
            self.iters = int(input("enter number of bananas: "))
            self.iters /= 26
            self.iters = int(self.iters)
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