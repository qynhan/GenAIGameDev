# GenAIGameDev
Undergraduate thesis in researching how using prompt engineering can act as Non-Player-Characters (NPC)

# System Design and Architecture Documentation

## 1. Design Patterns Used

### 1.1 Component Pattern
- **Implementation**: The game is divided into distinct components (Player, Enemy, Coin, Gun) that operate independently.
- **Rationale**: Enables better maintainability and separation of concerns.
- **Example**:
```python
class Player:
    def __init__(self, pos, groups, collision_sprites)
    def input()
    def move(dt)
    def update(dt)
```

### 1.2 Observer Pattern
- **Implementation**: The sprite groups system observes and updates all game objects.
- **Rationale**: Provides efficient management of multiple game entities.
- **Example**:
```python
class AllSprites(pygame.sprite.Group):
    def draw(self, target_pos)
    def update(dt)
```

### 1.3 State Pattern
- **Implementation**: Player animation states (up, down, left, right)
- **Rationale**: Manages complex state transitions cleanly.
- **Example**:
```python
self.frames = {'left': [], 'right': [], 'up': [], 'down': []}
```

## 2. Component Interfaces

### 2.1 Sprite Interface
```python
class pygame.sprite.Sprite:
    image: Surface  # Visual representation
    rect: Rect      # Position and collision
    update(dt)      # Update logic
```

### 2.2 Group Management Interface
```python
class AllSprites:
    display_surface: Surface
    offset: Vector2
    draw(target_pos)
```

### 2.3 Game Manager Interface
```python
class Game:
    running: bool
    all_sprites: AllSprites
    update(dt)
    draw()
```

## 3. Quality Attributes

### 3.1 Performance
- **Implementation**: 
  - Sprite Group optimization for rendering
  - Asynchronous API calls for enemy movement
  - Efficient collision detection using spatial partitioning
- **Example**:
```python
def async_calc_next_enemy_moves(self, num_moves=50):
    thread = threading.Thread(target=fetch_moves, daemon=True)
```

### 3.2 Usability
- **Implementation**:
  - Intuitive controls (WASD/Arrow keys)
  - Visual feedback for coin collection
  - Clear game over screen with restart option
- **Example**:
```python
def draw_game_over_screen(self):
    score_text = f"Final Coins: {self.coins_collected}"
    button_text = "Restart Game"
```

### 3.3 Reliability
- **Implementation**:
  - Error handling for API calls
  - Fallback systems for enemy movement
  - State persistence for high scores
- **Example**:
```python
def fallback_enemy_moves(self, num_moves):
    # Fallback logic when API fails
```

### 3.4 Modularity
- **Implementation**:
  - Separate classes for different game entities
  - Clear separation of concerns
  - Reusable components
- **Example**: The class diagram shows clear separation of responsibilities

## 4. Design Decisions Rationale

### 4.1 Asynchronous API Integration
- **Decision**: Use threading for API calls
- **Rationale**: 
  - Prevents game freezing during API calls
  - Maintains smooth gameplay
  - Handles API rate limiting gracefully

### 4.2 Sprite-based Architecture
- **Decision**: Use Pygame's sprite system
- **Rationale**:
  - Efficient collision detection
  - Built-in group management
  - Standard game development practice

### 4.3 Component-based Design
- **Decision**: Separate game elements into components
- **Rationale**:
  - Easier maintenance
  - Better testing capabilities
  - Simplified feature additions

### 4.4 State Management
- **Decision**: Centralized game state in Game class
- **Rationale**:
  - Single source of truth
  - Easier debugging
  - Simplified state transitions

## 5. Future Considerations

### 5.1 Scalability
- Support for multiple levels
- Additional game modes
- Online multiplayer capabilities

### 5.2 Maintainability
- Documentation standards
- Code review processes
- Testing framework integration

### 5.3 Performance Optimization
- Asset loading optimization
- Rendering pipeline improvements
- Memory management strategies
