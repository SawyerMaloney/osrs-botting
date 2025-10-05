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

        self.log_out_template = self.load_template("log_out.png")
        self.log_out_location = None
        
        self.log_out_button_template = self.load_template("log_out_button.png")
        self.log_out_button_location = None

        self.inventory_template = self.load_template("inventory.png")
        self.inventory_loc = None

        self.inv_top_left_template = self.load_template("inv_top_left.png")
        self.inv_top_left_loc = None

        self.inv_bottom_right_template = self.load_template("inv_bottom_right.png")
        self.inv_bottom_right_loc = None

        # array of positions for each item. 24 items total, 4 W x 7 H 
        self.inv_positions = [[None for _ in range(4)] for _ in range(7)]

        self.cached_region = None
        self.debug_counter = 0

        self.debug_folder = "debug"
        os.makedirs(self.debug_folder, exist_ok=True)

        print("Need to setup client macro locations. Please setup your window as you will have it while botting, then press space.")
        with keyboard.Listener(on_press=self.setup_macros) as listener:
            listener.join()

        self.calculate_inv_slot_pos()

        self.open_inventory_tab()
        self.reset_mouse()

        self.inv_pos_count = 0

    def calculate_inv_slot_pos(self):
        self.inv_width = self.inv_bottom_right_loc[0] - self.inv_top_left_loc[0]
        self.inv_height = self.inv_bottom_right_loc[1] - self.inv_top_left_loc[1]
        self.inv_offset_x = self.inv_width / 8
        self.inv_offset_y = self.inv_height / 14

        print(f"inv_top_left[1]: {self.inv_top_left_loc[1]}, offset_y: {self.inv_offset_y}, inv_height: {self.inv_height}")

        for h in range(len(self.inv_positions)):
            for w in range(len(self.inv_positions[0])):
                item_pos = (self.inv_offset_x + w * self.inv_width / 4 + self.inv_top_left_loc[0], self.inv_offset_y + h * self.inv_height / 7 + self.inv_top_left_loc[1])
                self.inv_positions[h][w] = item_pos

        print(f"Finished calculating item positions: \n{self.inv_positions}")

    def load_template(self, template_name):
        template = cv2.imread(self.template_path(template_name), cv2.IMREAD_UNCHANGED)
        template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
        return template

    def setup_macros(self, key):
        """
            Find and save different locations on the screen that won't change.
        """
        if key == keyboard.Key.space:
            with mss.mss() as sct:
                # inventory location
                print("Finding inventory location...")
                status, self.inventory_loc, top_left, bottom_right = self.block_on_go_to_image(sct, self.inventory_template, False, click=False, move=False, debug=True)
                print(f"successfully found inventory location at {self.inventory_loc}")
                print("Finding logout menu location...")
                status, self.log_out_location, top_left, bottom_right = self.block_on_go_to_image(sct, self.log_out_template, False, click=True, move=True, debug=True)
                print(f"Successfully found logout menu button at {self.log_out_location}.")
                print("Finding logout button location...")
                status, self.log_out_button_location, top_left, bottom_right = self.block_on_go_to_image(sct, self.log_out_button_template, False, click=False, move=False, debug=True)
                print(f"Successfully found logout button at {self.log_out_button_location}")
                # because of the return value of 'go_to_image', we have a weird assignment
                print("Finding top left of inventory...")
                status, center, top_left, self.inv_top_left_loc = self.block_on_go_to_image(sct, self.inv_top_left_template, False, click=False, move=False, debug=True)
                print(f"Successfully found top left of inventory at {self.inv_top_left_loc}")
                print("Finding bottom right of inventory...")
                status, center, self.inv_bottom_right_loc, bottom_right = self.block_on_go_to_image(sct, self.inv_bottom_right_template, False, click=False, move=False, debug=True)
                print(f"Successfully found bottom right of inventory at {self.inv_bottom_right_loc}")
                return False

    def template_path(self, template_name):
        return os.path.join("images", template_name)

    def left_click(self):
        self.mouse_ctrl.click(mouse.Button.left, 1)

    def move_mouse(self, loc):
        self.mouse_ctrl.position = loc

    def wait(self, default_wait=.5):
        time.sleep(default_wait + random.random())

    def block_on_go_to_image(self, sct, image, caching, click=True, move=True, threshold=.8, debug=False):
        status, center, top_left, bottom_right = self.go_to_image(sct, image, caching, click=click, move=move, threshold=threshold, debug=debug)
        while not status:
            status, center, top_left, bottom_right = self.go_to_image(sct, image, caching, click=click, move=move, threshold=threshold, debug=debug)
        return status, center, top_left, bottom_right

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
            bottom_right = (max_loc[0] + t_width, max_loc[1] + t_height)
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
            return True, (center_x, center_y), max_loc, bottom_right
        else:
            if debug:
                print(f"no good match, max val {max_val} with threshold {threshold}")
            return False, (0, 0), (0, 0), (0, 0) # no good match
        
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

    def use_item(self, w, h):
        print(f"using item {w}, {h}")
        print(f"w: {self.inv_positions[h][w][1]}, h: {self.inv_positions[h][w][0]}")
        self.move_mouse(self.inv_positions[h][w])
        self.wait()
        self.left_click()
        self.wait()

    def has_item(self, w, h, debug=False):
        item_loc = self.inv_positions[h][w]
        # find size of item 
        item_size = (self.inv_width / 4, self.inv_height / 7)
        # find top left of the position
        item_top_left = (int(item_loc[0] - item_size[0]/2), int(item_loc[1] - item_size[0]/2))
        item_bottom_right = (int(item_loc[0] + item_size[0] / 2), int(item_loc[1] + item_size[1] / 2))
        # now search 
        region = {'top': item_top_left[1], 'left': item_top_left[0], 'width': int(item_size[1]), 'height': int(item_size[0])}
        print(f"searching region {region}")
        if debug:
            with mss.mss() as sct:
                screen = np.array(sct.grab(sct.monitors[1]))
            
            # convert to grayscale for edge detection
            gray = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)

            # crop the item region from the grayscale image to check edges
            item_crop = gray[item_top_left[1]:item_bottom_right[1], item_top_left[0]:item_bottom_right[0]]
            edges = cv2.Canny(item_crop, 100, 200)
            edge_density = np.count_nonzero(edges) / edges.size
            print(f"Edge density: {edge_density:.4f}")
            # draw a rectangle on the full screen to show the grabbed region
            screen_bgr = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
            cv2.rectangle(screen_bgr, item_top_left, item_bottom_right, (0, 0, 255), 2)

            # save the screenshot with highlighted item
            cv2.imwrite(f"screenshot_with_box_{self.inv_pos_count}.png", screen_bgr)
            print(f"Saved screenshot with bounding box as screenshot_with_box_{self.inv_pos_count}.png")
            self.inv_pos_count += 1
        else:
            with mss.mss() as sct:
                img = np.array(sct.grab(region))

            # Convert from BGRA (used by mss) to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

            # Run edge detection (Canny is fast and robust)
            edges = cv2.Canny(gray, 100, 200)

            # Compute how many pixels are edges
            edge_density = np.count_nonzero(edges) / edges.size
            print(f"Edge density: {edge_density:.4f}")

        # Decide threshold (tweak as needed)
        if edge_density < 0.01:
            print("🟩 Likely blank area")
            return False
        else:
            print("🟥 Has edges or texture")
            return True