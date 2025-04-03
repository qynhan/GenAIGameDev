import threading
from random import randint
import pygame
from os.path import join
from settings import *
import json
from pytmx.util_pygame import load_pygame

class Coin(pygame.sprite.Sprite):
    """Class for coin objects."""
    def __init__(self, pos, image, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)

class CoinManager:
    def __init__(self, player, display_surface, font, tile_size, window_width, window_height, all_sprites):
        self.player = player
        self.display_surface = display_surface
        self.font = font
        self.tile_size = tile_size
        self.window_width = window_width
        self.window_height = window_height
        self.all_sprites = all_sprites  # Store reference to all_sprites group

        self.coin_sprites = pygame.sprite.Group()
        self.coins_collected = 0
        self.coin_collect_sound = pygame.mixer.Sound(join('audio', 'coinCollect.mp3'))
        self.coin_collect_sound.set_volume(0.5)
        self.coin_image = pygame.image.load(join('images', 'gameplay', 'coin.png')).convert_alpha()

        self.coin_generation_interval = 10000  # 10 seconds in milliseconds
        self.last_coin_generation_time = pygame.time.get_ticks()

        self.stop_threads = False
        self.threads = []

        self.high_score = self.load_high_score()  # Load high score from file

    def load_high_score(self):
        """Load the high score from a file."""
        try:
            with open('high_score.txt', 'r') as file:
                return int(file.read().strip())
        except (FileNotFoundError, ValueError):
            return 0  # Default to 0 if file doesn't exist or is invalid

    def save_high_score(self):
        """Save the high score to a file."""
        with open('high_score.txt', 'w') as file:
            file.write(str(self.high_score))

    def update_high_score(self):
        """Update the high score if the current score exceeds it."""
        if self.coins_collected > self.high_score:
            self.high_score = self.coins_collected
            self.save_high_score()
            print(f"[DEBUG] New high score: {self.high_score}")

    def generate_coins(self, camera_offset, num_coins=10):
        """Generate coin positions within the visible camera region."""
        def fetch_coin_positions():
            if self.stop_threads:
                print("[DEBUG] Stop signal received. Exiting coin generation thread.")
                return

            camera_min_x, camera_min_y = camera_offset
            camera_max_x = camera_min_x + self.window_width
            camera_max_y = camera_min_y + self.window_height

            for _ in range(num_coins):
                coin_x = randint(camera_min_x // self.tile_size, camera_max_x // self.tile_size) * self.tile_size
                coin_y = randint(camera_min_y // self.tile_size, camera_max_y // self.tile_size) * self.tile_size
                coin = Coin((coin_x, coin_y), self.coin_image, self.coin_sprites)
                self.coin_sprites.add(coin)
                self.all_sprites.add(coin)  # Add coin to all_sprites group

        thread = threading.Thread(target=fetch_coin_positions, daemon=True)
        self.threads.append(thread)
        thread.start()

    def generate_coins_with_gemini(self, camera_offset, num_coins=10, gemini_client=None, gemini_api_key=None):
        """Generate coin positions using the Gemini API."""
        def fetch_coin_positions():
            while not self.stop_threads:  # Check stop signal
                if not gemini_client or not gemini_api_key:
                    print("[DEBUG] Gemini client or API key not provided.")
                    return

                # Prepare map layout and camera region
                camera_min_x, camera_min_y = camera_offset
                camera_max_x = camera_min_x + self.window_width
                camera_max_y = camera_min_y + self.window_height
                map_layout = self.get_relevant_map_layout(camera_offset, radius=10)

                # Create the request payload
                request_data = {
                    "map_layout": map_layout,
                    "camera_region": {
                        "x_min": camera_min_x,
                        "y_min": camera_min_y,
                        "x_max": camera_max_x,
                        "y_max": camera_max_y
                    },
                    "num_coins": num_coins
                }

                # Define the schema for the response
                coin_schema = {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"}
                    },
                    "required": ["x", "y"]
                }

                schema_dict = {
                    "type": "array",
                    "items": coin_schema
                }

                # Call Gemini API
                try:
                    prompt = f"""Given the following data:\n
                                 Map layout: {map_layout}\n
                                 Camera region: {request_data['camera_region']}\n
                                 Generate {num_coins} coin positions in areas without obstacles. 
                                 Return the result as a JSON list of objects with 'x' and 'y' coordinates."""

                    client = gemini_client(api_key=gemini_api_key)
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt,
                        config={
                            'response_mime_type': 'application/json',
                            'response_schema': schema_dict,
                        }
                    )

                    # Parse the response
                    data = json.loads(response.text)
                    if isinstance(data, list):
                        for coin_data in data:
                            # Add larger randomness to the coin positions
                            random_offset_x = randint(-self.tile_size, self.tile_size)
                            random_offset_y = randint(-self.tile_size, self.tile_size)
                            coin_x = coin_data["x"] + random_offset_x
                            coin_y = coin_data["y"] + random_offset_y

                            # Ensure the coin stays within the camera region
                            coin_x = max(camera_min_x, min(coin_x, camera_max_x))
                            coin_y = max(camera_min_y, min(coin_y, camera_max_y))

                            coin = Coin((coin_x, coin_y), self.coin_image, self.coin_sprites)
                            self.coin_sprites.add(coin)
                            self.all_sprites.add(coin)  # Add coin to all_sprites group
                        print("[DEBUG] Coins generated successfully using Gemini API with larger random offsets.")
                    else:
                        print("[DEBUG] Invalid response format:", data)

                except Exception as e:
                    print(f"[DEBUG] Error calling Gemini API for coin generation: {e}")
                break  # Exit the loop after one successful API call

        thread = threading.Thread(target=fetch_coin_positions, daemon=True)
        self.threads.append(thread)
        thread.start()

    def get_relevant_map_layout(self, camera_offset, radius):
        """Generate a smaller map layout around the camera region."""
        map_layout = self.get_map_layout()
        relevant_layout = {}
        camera_min_x, camera_min_y = camera_offset
        camera_max_x = camera_min_x + self.window_width
        camera_max_y = camera_min_y + self.window_height

        for (x, y), value in map_layout.items():
            if camera_min_x // self.tile_size <= x <= camera_max_x // self.tile_size and \
               camera_min_y // self.tile_size <= y <= camera_max_y // self.tile_size:
                relevant_layout[(x, y)] = value
        return relevant_layout

    def get_map_layout(self):
        """Generate a grid representation of the map."""
        map_layout = {}
        for x, y, _ in load_pygame(join('data', 'maps', 'world.tmx')).get_layer_by_name('Ground').tiles():
            map_layout[(x, y)] = 0  # Walkable tile
        for obj in load_pygame(join('data', 'maps', 'world.tmx')).get_layer_by_name('Collisions'):
            grid_x, grid_y = int(obj.x // self.tile_size), int(obj.y // self.tile_size)
            map_layout[(grid_x, grid_y)] = 1  # Obstacle
        return map_layout

    def collect_coins(self):
        """Check if the player collects any coins."""
        collected_coins = pygame.sprite.spritecollide(self.player, self.coin_sprites, True, pygame.sprite.collide_mask)
        if collected_coins:
            self.coin_collect_sound.play()
            self.coins_collected += len(collected_coins)
            print(f"[DEBUG] Coins collected this session: {self.coins_collected}")
            self.update_high_score()  # Update high score after collecting coins

    def draw_coin_tracker(self):
        """Draw the coin tracker and high score at the bottom of the screen."""
        tracker_text = f"Coins Collected: {self.coins_collected} | High Score: {self.high_score}"
        tracker_surface = self.font.render(tracker_text, True, (255, 255, 255))
        tracker_rect = tracker_surface.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
        self.display_surface.blit(tracker_surface, tracker_rect)

    def stop_all_threads(self):
        """Signal threads to stop and wait for them to exit."""
        self.stop_threads = True
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)
