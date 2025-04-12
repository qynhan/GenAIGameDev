# GenAI Coin Hunter: Undergraduate Thesis Project

## Overview

**GenAI Coin Hunter** is a 2D game developed as part of an undergraduate thesis project. The game integrates **Generative AI** to dynamically generate enemy movements and coin placements, creating a unique and engaging gameplay experience. Built using Python and Pygame, the project demonstrates the potential of combining traditional game development techniques with cutting-edge AI technologies.

## Features

- **Dynamic Enemy AI**: Enemies use AI-generated paths to navigate toward the player while avoiding obstacles.
- **Coin Collection System**: Coins are dynamically spawned on the map, and players can collect them to increase their score.
- **High Score Tracking**: Tracks the player's highest score across sessions.
- **Asynchronous API Integration**: Uses Google's Gemini AI for real-time enemy movement and coin placement.
- **Player Feedback Integration**:
  - Space bar for shooting.
  - Slower enemy speed for easier gameplay.
  - Enemies do not spawn near the player.
  - Coin tracker to display collected coins.

## Technologies Used

- **Programming Language**: Python
- **Game Framework**: Pygame
- **AI Integration**: Google Gemini AI
- **Data Validation**: Pydantic
- **Map Design**: Tiled Map Editor
- **Audio Editing**: Audacity

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/GenAI-Coin-Hunter.git
   cd GenAI-Coin-Hunter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the environment:
   - Create a `.env` file in the root directory.
   - Add your Google Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

4. Run the game:
   ```bash
   python main.py
   ```

## Gameplay Instructions

- **Movement**: Use `W`, `A`, `S`, `D` or arrow keys to move the player.
- **Shooting**: Press the `Space` bar to shoot bullets at enemies.
- **Objective**: Collect as many coins as possible while avoiding enemies.
- **Game Over**: The game ends when the player collides with an enemy. You can restart the game from the game-over screen.

## Key Features in Detail

### 1. Generative AI Integration
- **Enemy Movement**: Enemies use AI-generated paths to navigate toward the player while avoiding obstacles.
- **Coin Placement**: Coins are dynamically placed on the map using AI, ensuring they are accessible and evenly distributed.

### 2. Player Feedback Integration
- Adjusted controls and gameplay mechanics based on player feedback:
  - Space bar for shooting instead of the left mouse button.
  - Slower enemy speed for a more balanced difficulty.
  - Enemies spawn at a safe distance from the player.
  - Added a coin tracker to display the number of coins collected.

### 3. High Score Tracking
- Tracks the highest number of coins collected across all game sessions.
- Displays the high score on the game-over screen.

### 4. Asynchronous API Calls
- Uses threading to fetch AI-generated data without interrupting gameplay.
- Implements rate-limiting and fallback mechanisms to ensure smooth performance.

## File Structure

```
GenAI-Coin-Hunter/
├── code/
│   ├── main.py          # Main game loop and logic
│   ├── player.py        # Player class and movement logic
│   ├── sprites.py       # Enemy, bullet, and gun classes
│   ├── coin.py          # Coin and CoinManager classes
│   ├── groups.py        # Custom sprite group for rendering
│   ├── settings.py      # Game settings and constants
├── data/
│   ├── maps/            # Tiled map files
│   ├── images/          # Game assets (player, enemies, coins, etc.)
│   ├── audio/           # Sound effects and background music
├── .env                 # Environment variables (API key)
├── requirements.txt     # Python dependencies
├── README.md            # Project documentation
```

## Testing and Validation

- **Unit Testing**: Tested individual components like `Player`, `Enemy`, and `CoinManager`.
- **Integration Testing**: Verified interactions between components, such as bullet collisions and coin collection.
- **Regression Testing**: Ensured existing features worked after implementing new ones.
- **Acceptance Testing**: Conducted playtesting sessions to gather feedback and improve gameplay.

## Future Enhancements

- **Obstacle Interaction**: Enemies can hide behind obstacles when under attack.
- **Multiplayer Mode**: Add support for cooperative or competitive gameplay.
- **Advanced AI**: Use more sophisticated AI models for enemy behavior.
- **Level Progression**: Introduce multiple levels with increasing difficulty.

## Acknowledgments

- **Prof. Mike Katchabaw** for his encouragments and support throughout this project.


---

Enjoy playing **GenAI Coin Hunter**! If you have any feedback or suggestions, feel free to open an issue or submit a pull request.
