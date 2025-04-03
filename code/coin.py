import threading
from random import randint
import pygame
from os.path import join
from settings import *

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

    def collect_coins(self):
        """Check if the player collects any coins."""
        collected_coins = pygame.sprite.spritecollide(self.player, self.coin_sprites, True, pygame.sprite.collide_mask)
        if collected_coins:
            self.coin_collect_sound.play()
            self.coins_collected += len(collected_coins)
            print(f"[DEBUG] Coins collected this session: {self.coins_collected}")

    def draw_coin_tracker(self):
        """Draw the coin tracker at the bottom of the screen."""
        tracker_text = f"Coins Collected: {self.coins_collected}"
        tracker_surface = self.font.render(tracker_text, True, (255, 255, 255))
        tracker_rect = tracker_surface.get_rect(midbottom=(self.window_width // 2, self.window_height - 10))
        self.display_surface.blit(tracker_surface, tracker_rect)

    def stop_all_threads(self):
        """Signal threads to stop and wait for them to exit."""
        self.stop_threads = True
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)
