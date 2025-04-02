import threading  # Add threading for asynchronous API calls

# import backend
from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites

from random import randint, choice

from google import genai
import os
from dotenv import load_dotenv
import json  

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
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.running = False

    def calc_next_enemy_move(self, num_moves=50):
        """Calculate the next `num_moves` moves for each enemy using the Gemini API."""
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

        # Call Gemini API
        client = genai.Client(api_key=self.gemini_api_key)
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Given the following data:\n"
                         f"Enemy positions: {enemy_positions}\n"
                         f"Player position: {player_position}\n"
                         f"Map layout: {map_layout}\n"
                         f"Calculate the next {num_moves} optimal positions for the enemies to navigate toward the player while avoiding obstacles. "
                         f"Return the result as a JSON list of lists where each sublist contains the next positions of all enemies.",
            )
            # Clean the response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()  # Remove ```json and trailing ```
            
            # Parse the response
            next_moves = json.loads(response_text)  # Safely parse JSON response
            return next_moves
        except json.JSONDecodeError:
            print("Invalid JSON response from Gemini API:", response.text)
            return None
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None

    def async_calc_next_enemy_moves(self, num_moves=50):
        """Fetch the next `num_moves` moves asynchronously."""
        def fetch_moves():
            new_moves = self.calc_next_enemy_move(num_moves)
            if new_moves:
                self.enemy_moves = new_moves
            else:
                print("API response delayed or invalid. Falling back to simple logic.")
                self.fallback_enemy_moves(num_moves)

        thread = threading.Thread(target=fetch_moves)
        thread.start()

    def fallback_enemy_moves(self, num_moves):
        """Generate simple fallback moves for enemies."""
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
        while self.running:
            # dt
            dt = self.clock.tick() / 1000

            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == self.enemy_event:
                    Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

            # Use precomputed moves or fetch new ones if needed
            if not self.enemy_moves or len(self.enemy_moves[0]) == 0:
                self.async_calc_next_enemy_moves(num_moves=50)

            if self.enemy_moves:
                for enemy, moves in zip(self.enemy_sprites, self.enemy_moves):
                    if moves:
                        next_pos = moves.pop(0)
                        enemy.rect.center = next_pos

            # update
            self.gun_timer()
            self.input()
            self.all_sprites.update(dt)
            self.bullet_collision()
            self.player_collision()

            # draw
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            pygame.display.update()
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()