import threading  # Add threading for asynchronous API calls
import time  # Add time module for rate-limiting

# import backend
from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from coin import CoinManager

from random import randint, choice

from google import genai
import os
from dotenv import load_dotenv
import json
from pydantic import BaseModel, conlist
from typing import List, Tuple, Union


class Move(BaseModel):
    x: int
    y: int


class MoveList(BaseModel):
    moves: List[Move]

class Game:
    def __init__(self):
        print("initializing the game, in Game constructor")
        # setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('GenAI Survivor Game -- Undergrad Thesis Project')
        self.clock = pygame.time.Clock()
        self.running = True

        # initialize Gemini API Key
        load_dotenv()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        self.font = pygame.font.Font(None, 36)  # Add this line before using self.font

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        # gun timer
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 100 # milliseconds

        # enemy timer
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 300)
        self.spawn_positions = []

        # audio
        self.shoot_sound = pygame.mixer.Sound(join('audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.4)
        self.impact_sound = pygame.mixer.Sound(join('audio', 'impact.ogg'))
        self.music = pygame.mixer.Sound(join('audio', 'music.wav'))
        self.music.set_volume(0.3)
        self.music.play(loops = -1)

        # setup
        self.load_images()
        self.setup()
        self.enemy_moves = []  # Initialize precomputed moves for enemies
        self.api_call_timestamps = []  # Track API call timestamps
        self.api_lock = threading.Lock()  # Lock for thread-safe access
        self.threads = []  # Store threads for proper management
        self.stop_threads = False  # Signal to stop threads

        # Coin manager
        self.coin_manager = CoinManager(
            player=self.player,
            display_surface=self.display_surface,
            font=self.font,
            tile_size=TILE_SIZE,
            window_width=WINDOW_WIDTH,
            window_height=WINDOW_HEIGHT,
            all_sprites=self.all_sprites  # Pass all_sprites group to CoinManager
        )
        
    def load_images(self):
        self.bullet_surf =  pygame.image.load(join('images', 'gun', 'bullet.png')).convert_alpha()

        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key= lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)
        
    
    def input(self):
        keys = pygame.key.get_pressed()
        if (int(keys[pygame.K_SPACE]) or pygame.mouse.get_pressed()[0]) and self.can_shoot:
            self.shoot_sound.play()
            pos = self.gun.rect.center + self.gun.shooting_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.shooting_direction, (self.all_sprites, self.bullet_sprites)) 
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True


    def setup(self):
        map = load_pygame(join('data', 'maps', 'world.tmx'))
        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))
                    
    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        sprite.destroy()
                    bullet.kill()
    
    def player_collision(self):
        """Check if the player collides with any enemy."""
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            # print("[DEBUG] Player collided with an enemy. Stopping game.")
            self.running = False
            self.stop_threads = True  # Signal threads to stop
            return True  # Indicate that a collision occurred
        return False

    def calc_next_enemy_move(self, num_moves=50):
        """Calculate the next `num_moves` moves for each enemy using the Gemini API with JSON schema."""
        # Prepare data to send to Gemini
        enemy_positions = [(enemy.rect.centerx, enemy.rect.centery) for enemy in self.enemy_sprites]

        # Convert player's position to map-relative coordinates
        camera_offset_x, camera_offset_y = self.get_camera_offset()
        player_position = (
            self.player.rect.centerx + camera_offset_x,
            self.player.rect.centery + camera_offset_y
        )

        # Clamp player position to map boundaries
        map_width, map_height = self.get_map_dimensions()
        player_position = (
            max(0, min(player_position[0], map_width - 1)),
            max(0, min(player_position[1], map_height - 1))
        )

        # Send only a smaller region of the map around the player and enemies
        map_layout = self.get_relevant_map_layout(player_position, radius=10)

        # Create the request payload
        request_data = {
            "enemy_positions": enemy_positions,
            "player_position": player_position,
            "map_layout": map_layout,
            "num_moves": num_moves
        }

        # Define the schema explicitly as a dictionary
        move_schema = {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"}
            },
            "required": ["x", "y"]
        }

        move_list_schema = {
            "type": "object",
            "properties": {
                "moves": {
                    "type": "array",
                    "items": move_schema
                }
            },
            "required": ["moves"]
        }

        schema_dict = {
            "type": "array",
            "items": move_list_schema
        }

        # Call Gemini API with retry logic
        client = genai.Client(api_key=self.gemini_api_key)
        retries = 3
        for attempt in range(retries):
            try:
                # print(f"[DEBUG] Sending request to Gemini API (Attempt {attempt + 1}).")
                # Simplified prompt
                prompt = f"""Given the following data:\n
                             Enemy positions: {enemy_positions}\n
                             Player position: {player_position}\n
                             Map layout: {map_layout}\n
                             Calculate the next {num_moves} optimal positions for the enemies to navigate toward the player while avoiding obstacles. 
                             Return the result as a JSON list of MoveList objects."""

                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': schema_dict,
                    }
                )
                # print("[DEBUG] Received raw response from Gemini API:", response.text)

                # Attempt to parse the entire response as a list of MoveList objects
                try:
                    data = json.loads(response.text)
                    if isinstance(data, list):
                        # Use Pydantic to parse the data
                        move_lists = [MoveList.parse_obj(item) for item in data]

                        next_moves = [[(move.x, move.y) for move in move_list.moves] for move_list in move_lists]
                        # print("[DEBUG] Received enemy moves from Gemini API successfully.")
                        return next_moves
                    else:
                        print("[DEBUG] Response is not a list:", data)
                        return None
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSONDecodeError: {e}")
                    print(f"[DEBUG] Raw response: {response.text}")
                    return None
                except Exception as e:
                    print(f"[DEBUG] Pydantic parsing error: {e}")
                    return None

            except Exception as e:
                print(f"[DEBUG] Error calling Gemini API: {e}")
                if "502" in str(e) and attempt < retries - 1:
                    print("[DEBUG] Retrying due to server error...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None

        print("[DEBUG] All retry attempts failed.")
        return None

    def async_calc_next_enemy_moves(self, num_moves=50):
        """Fetch the next `num_moves` moves asynchronously with rate-limiting."""
        def fetch_moves():
            # print("[DEBUG] Thread started for fetching enemy moves.")
            while not self.stop_threads:  # Check stop signal
                # Rate-limiting logic
                current_time = time.time()
                with self.api_lock:  # Ensure thread-safe access
                    self.api_call_timestamps = [
                        t for t in self.api_call_timestamps if current_time - t < 60
                    ]  # Keep only timestamps within the last 60 seconds

                    if len(self.api_call_timestamps) >= 15:
                        # print("[DEBUG] Rate limit reached. Falling back to simple logic.")
                        self.fallback_enemy_moves(num_moves)
                        return

                    # Proceed with API call
                    self.api_call_timestamps.append(current_time)

                # print("[DEBUG] Making API call to calculate enemy moves.")
                new_moves = self.calc_next_enemy_move(num_moves)
                if self.stop_threads:  # Exit immediately if stop signal is set
                    # print("[DEBUG] Stop signal received. Exiting thread.")
                    return
                if new_moves:
                    # print("[DEBUG] Successfully fetched enemy moves from API.")
                    self.enemy_moves = new_moves
                else:
                    # print("[DEBUG] API response delayed or invalid. Falling back to simple logic.")
                    self.fallback_enemy_moves(num_moves)
                break  # Exit the loop after fetching moves
            # print("[DEBUG] Thread exiting.")

        if self.stop_threads:  # Avoid creating new threads if stop signal is set
            # print("[DEBUG] Stop signal set. Not starting new thread.")
            return

        thread = threading.Thread(target=fetch_moves, daemon=True)  # Mark thread as daemon
        self.threads.append(thread)
        # print("[DEBUG] Starting new thread for enemy move calculation.")
        thread.start()

    def fallback_enemy_moves(self, num_moves):
        """Generate simple fallback moves for enemies."""
        if self.stop_threads:  # Exit immediately if stop signal is set
            # print("[DEBUG] Stop signal received. Exiting fallback logic.")
            return
        self.enemy_moves = []  # Reset enemy moves
        for enemy in self.enemy_sprites:
            moves = []
            for _ in range(num_moves):
                # Move enemy directly toward the player
                dx = self.player.rect.centerx - enemy.rect.centerx
                dy = self.player.rect.centery - enemy.rect.centery
                step_x = dx // abs(dx) if dx != 0 else 0
                step_y = dy // abs(dy) if dy != 0 else 0
                moves.append((enemy.rect.centerx + step_x, enemy.rect.centery + step_y))
            self.enemy_moves.append(moves)

    def get_relevant_map_layout(self, player_position, radius):
        """Generate a smaller map layout around the player."""
        map_layout = self.get_map_layout()
        relevant_layout = {}
        px, py = player_position
        for (x, y), value in map_layout.items():
            if abs(x - px // TILE_SIZE) <= radius and abs(y - py // TILE_SIZE) <= radius:
                relevant_layout[(x, y)] = value
        return relevant_layout

    def get_camera_offset(self):
        """Calculate the camera's offset relative to the map."""
        # camera centers on the player
        camera_x = self.player.rect.centerx - (WINDOW_WIDTH // 2)
        camera_y = self.player.rect.centery - (WINDOW_HEIGHT // 2)
        return camera_x, camera_y

    def get_map_layout(self):
        """Generate a grid representation of the map."""
        map_layout = {}
        for x, y, _ in load_pygame(join('data', 'maps', 'world.tmx')).get_layer_by_name('Ground').tiles():
            map_layout[(x, y)] = 0  # Walkable tile
        for obj in load_pygame(join('data', 'maps', 'world.tmx')).get_layer_by_name('Collisions'):
            grid_x, grid_y = int(obj.x // TILE_SIZE), int(obj.y // TILE_SIZE)
            map_layout[(grid_x, grid_y)] = 1  # Obstacle
        return map_layout

    def get_map_dimensions(self):
        """Get the dimensions of the map in pixels."""
        map = load_pygame(join('data', 'maps', 'world.tmx'))
        map_width = map.width * TILE_SIZE
        map_height = map.height * TILE_SIZE
        return map_width, map_height

    def run(self):
        # print("[DEBUG] Game loop started.")
        self.coin_manager.generate_coins_with_gemini(
            self.get_camera_offset(),
            10,
            gemini_client=genai.Client,
            gemini_api_key=self.gemini_api_key
        )  # Generate initial coins using Gemini API

        while self.running:
            # dt
            dt = self.clock.tick() / 1000

            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # print("[DEBUG] Quit event detected. Stopping game.")
                    self.running = False
                if event.type == self.enemy_event:
                    # print("[DEBUG] Spawning new enemy.")
                    Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

            # Use precomputed moves or fetch new ones if needed
            if not self.enemy_moves or len(self.enemy_moves[0]) == 0:
                # print("[DEBUG] No precomputed moves available. Fetching new moves.")
                self.async_calc_next_enemy_moves(50)

            if self.enemy_moves:
                for enemy, moves in zip(self.enemy_sprites, self.enemy_moves):
                    if moves:
                        next_pos = moves.pop(0)
                        # print(f"[DEBUG] Moving enemy to position: {next_pos}.")
                        enemy.rect.center = next_pos

            # Periodic coin generation
            current_time = pygame.time.get_ticks()
            if current_time - self.coin_manager.last_coin_generation_time >= self.coin_manager.coin_generation_interval:
                self.coin_manager.generate_coins_with_gemini(
                    self.get_camera_offset(),
                    10,
                    gemini_client=genai.Client,
                    gemini_api_key=self.gemini_api_key
                )
                self.coin_manager.last_coin_generation_time = current_time

            # update
            self.gun_timer()
            self.input()
            self.all_sprites.update(dt)
            self.bullet_collision()
            self.coin_manager.collect_coins()  # Check for coin collection
            if self.player_collision():  # Exit immediately if a collision occurs
                # print("[DEBUG] Exiting game loop due to player collision.")
                break

            # draw
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)  # Draw map and enemies
            self.coin_manager.draw_coin_tracker()  # Keep this to show coin count
            pygame.display.update()

        # Signal threads to stop and wait for them to exit
        # print("[DEBUG] Stopping all threads.")
        self.stop_threads = True
        for thread in self.threads:
            if thread.is_alive():
                # print("[DEBUG] Waiting for thread to finish.")
                thread.join(timeout=1)  # Use a timeout to prevent indefinite blocking
        print("[DEBUG] Exiting game. Cleaning up.")
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()