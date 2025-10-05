import cv2
import numpy as np
import mss
import time
from pynput import mouse, keyboard
import random
from datetime import datetime
import os

class Bot:
    def __init__(self):
        self.mouse_ctrl = mouse.Controller()
        self.keyboard = keyboard.Controller()

        self.log_out_template = cv2.imread(self.template_path("log_out.png"), cv2.IMREAD_UNCHANGED)
        self.log_out_template = cv2.cvtColor(self.log_out_template, cv2.COLOR_BGRA2BGR)
        self.log_out_location = None

        self.log_out_button_template = cv2.imread(self.template_path("log_out_button.png"), cv2.IMREAD_UNCHANGED)
        self.log_out_button_template = cv2.cvtColor(self.log_out_button_template, cv2.COLOR_BGRA2BGR)
        self.log_out_button_location = None

        self.inventory_template = cv2.imread(self.template_path("inventory.png"), cv2.IMREAD_UNCHANGED)
        self.inventory_template = cv2.cvtColor(self.inventory_template, cv2.COLOR_BGRA2BGR)
        self.inventory_loc = None

        self.cached_region = None
        self.debug_counter = 0

        self.debug_folder = "debug"
        os.makedirs(self.debug_folder, exist_ok=True)

        print("Need to setup client macro locations. Please setup your window as you will have it while botting, then press space.")
        with keyboard.Listener(on_press=self.setup_macros) as listener:
            listener.join()

    def setup_macros(self, key):
        """
            Find and save different locations on the screen that won't change.
        """
        if key == keyboard.Key.space:
            with mss.mss() as sct:
                # inventory location
                setup_complete = True
                if self.inventory_loc is None:
                    print("Finding inventory location...")
                    status, self.inventory_loc = self.block_on_go_to_image(sct, self.inventory_template, False, click=False, move=False, debug=True)
                    if status:
                        print(f"successfully found inventory location at {self.inventory_loc}")
                    else:
                        print("Failed to find inventory location")
                        setup_complete = False
                if self.log_out_location is None:
                    print("Finding logout menu location...")
                    status, self.log_out_location = self.block_on_go_to_image(sct, self.log_out_template, False, click=True, move=True, debug=True)
                    if status:
                        print(f"Successfully found logout menu button at {self.log_out_location}.")
                    else:
                        setup_complete = False
                if self.log_out_button_location is None:
                    print("Finding logout button location...")
                    status, self.log_out_button_location = self.block_on_go_to_image(sct, self.log_out_button_template, False, click=False, move=False, debug=True)
                    if status:
                        print(f"Successfully found logout button at {self.log_out_button_location}")
                    else:
                        setup_complete = False

                if setup_complete:
                    print("Setup complete.")
                    self.open_inventory_tab()
                    return False  # opposite, because this will stop the listener
                else:
                    print("Setup did not complete. Please press space again when your screen is clear.")
                    return True


    def template_path(self, template_name):
        return os.path.join("images", template_name)

    def left_click(self):
        self.mouse_ctrl.click(mouse.Button.left, 1)

    def move_mouse(self, loc):
        self.mouse_ctrl.position = loc

    def wait(self, default_wait=.5):
        time.sleep(default_wait + random.random())

    def block_on_go_to_image(self, sct, image, caching, click=True, move=True, threshold=.8, debug=False):
        ret, pos = self.go_to_image(sct, image, caching, click=click, move=move, threshold=threshold, debug=debug)
        while not ret:
            ret, pos = self.go_to_image(sct, image, caching, click=click, move=move, threshold=threshold, debug=debug)
        return ret, pos

    def go_to_image(self, sct, image, caching, click=True, move=True, threshold=.8, debug=False):
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
            filename = os.path.join(self.debug_folder, f"debug_{self.debug_counter}.png")
            self.debug_counter += 1
            cv2.imwrite(filename, screenshot_vis)
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

            if move:
                print(f"moving to {center_x}, {center_y}...")
                self.move_mouse((center_x, center_y))
                self.wait()
            if click:
                print("clicking and waiting...")
                self.left_click()
                self.wait
           
            if debug:
                print(f"good match, max val {max_val} with threshold {threshold}")
            return True, (center_x, center_y)
        else:
            if debug:
                print(f"no good match, max val {max_val} with threshold {threshold}")
            return False, (0, 0) # no good match
        
    def log_out(self):
        if self.log_out_button_location is None or self.log_out_location is None:
            with mss.mss() as sct:
                print("Going to logout screen and clicking...")
                self.go_to_image(sct, self.log_out_template, False, debug=True, threshold=.2)
                print("waiting...")
                self.wait()
                print("Finding log out button and clicking...")
                img = self.go_to_image(sct, self.log_out_button_template, False, threshold=.5, debug=True)  # bye bye!
                while not img:
                    img = self.go_to_image(sct, self.log_out_button_template, False, threshold=.5, debug=True)  # bye bye!
                print("Log out pressed.")
                return True
        else:
            print("Going to logout menu.")
            self.move_mouse(self.log_out_location)
            self.wait()
            self.left_click()
            print("Pressing logout")
            self.move_mouse(self.log_out_button_location)
            self.wait()
            self.left_click()
        
    def open_magic_tab(self):
        self.keyboard.press(keyboard.Key.f6)
        self.keyboard.release(keyboard.Key.f6)
        
    def open_inventory_tab(self):
        if self.inventory_loc is None:
            with mss.mss() as sct:
                self.go_to_image(sct, self.inventory_template, False, threshold=.5, debug=True)
        else:
            self.move_mouse(self.inventory_loc)
            self.wait()
            self.left_click()

    def reset_mouse(self):
        self.move_mouse((0, 0))
        self.cached_region = None