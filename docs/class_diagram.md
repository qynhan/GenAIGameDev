# System Context Diagram

```mermaid
C4Context
    title System Context Diagram - GenAI Game System
    
    %% Layout configuration
    direction LR
    
    %% Core components with spacing
    Person(player, "Player", "User interaction")
    
    System(game, "GenAI Game\nSystem", "Core game engine")
    
    System_Ext(gemini, "Google\nGemini API", "AI service")
    
    %% Storage components
    SystemDb_Ext(assets, "Asset\nStorage", "Game resources")
    
    SystemDb(local, "Local\nStorage", "Game state")
    
    %% Relationships with spacing
    Rel_R(player, game, "Input")
    Rel_L(game, player, "Output")
    
    Rel_R(game, gemini, "AI Requests")
    Rel_L(gemini, game, "Decisions")
    
    Rel_D(game, assets, "Load")
    Rel_D(game, local, "Save")
```

# Game System Class Diagram

```mermaid
classDiagram

    class Game {
        -display_surface: Surface
        -clock: Clock
        -running: bool
        -gemini_api_key: str
        -all_sprites: AllSprites
        -collision_sprites: Group
        -bullet_sprites: Group
        -enemy_sprites: Group
        -player: Player
        -gun: Gun
        -coin_manager: CoinManager
        -enemy_moves: List
        +__init__()
        +setup()
        +run()
        +input()
        +calc_next_enemy_move()
        +async_calc_next_enemy_moves()
        +fallback_enemy_moves()
    }

    class Player {
        -pos: Vector2
        -direction: Vector2
        -speed: float
        +update(dt)
        +input()
    }

    class Gun {
        -player: Player
        -shooting_direction: Vector2
        +update()
    }

    class Enemy {
        -frames: List
        -player: Player
        -collision_sprites: Group
        +update(dt)
        +destroy()
    }

    class CoinManager {
        -player: Player
        -coins_collected: int
        -high_score: int
        +generate_coins_with_gemini()
        +collect_coins()
        +draw_coin_tracker()
    }

    class Move {
        +x: int
        +y: int
    }

    class MoveList {
        +moves: List[Move]
    }

    class AllSprites {
        -offset: Vector2
        +draw(target)
        +update(dt)
    }

    Game *-- Player : has
    Game *-- Gun : has
    Game *-- CoinManager : has
    Game o-- Enemy : manages
    Game *-- AllSprites : has
    Player --o Gun : references
    CoinManager --o Player : references
    Enemy --o Player : tracks
```

## Class Relationships

- **Game**: Central controller class that manages all game components
- **Player**: Represents the player character with movement controls
- **Gun**: Handles shooting mechanics, attached to the player
- **Enemy**: AI-controlled opponents that chase the player
- **CoinManager**: Manages coin generation and collection system
- **Move/MoveList**: Data structures for AI movement calculations
- **AllSprites**: Custom sprite group for offset-based rendering

## Key Features

1. **AI Integration**
   - Enemy movement calculation via Gemini API
   - Coin placement using AI suggestions
   - Fallback systems for API failures

2. **Game Mechanics**
   - Shooting system
   - Collision detection
   - Score tracking
   - Enemy spawning

3. **Technical Features**
   - Asynchronous API calls
   - Rate limiting protection
   - Thread management
   - State management
