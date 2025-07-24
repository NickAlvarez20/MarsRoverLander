Mars 3D Rover Landing Game
Overview
This is a 3D rover landing game built with Python and Pygame, where players guide a rover to land safely on a designated landing pad on Mars. Navigate through a field of asteroids, manage fuel, and control velocity to achieve a successful landing. The game features a first-person perspective with 3D projection, an atmospheric entry effect, and audio-visual feedback for immersion.
Features

3D Perspective Projection: Simulates a first-person view of the Martian surface with a landing pad and asteroids.
Physics-Based Gameplay: Includes gravity, thrust controls, and fuel management.
Asteroid Field: 2000 randomly generated asteroids with collision detection and proximity warnings.
Audio Feedback: Includes thruster sounds, win/lose effects, background music, and asteroid proximity alerts.
Visual Effects: 
Dynamic background transitioning from space to Mars' surface.
Landing pad with 3D details (raised edges, red 'X', grid texture).
Animated win sequence with an astronaut exiting the lander.


HUD: Displays altitude, fuel, velocity, and speed, with directional arrows for navigation.
Intro Animation: Fades in/out with an optional intro image.
Fullscreen Support: Toggle with F11 key.

Requirements

Python 3.x
Pygame: Install via pip install pygame
Optional Assets:
asteroid.png: Asteroid sprite (fallback to drawn circles if missing).
mars_background.jpg: Mars surface background (fallback to gradient if missing).
intro_image.jpg: Intro screen image (skipped if missing).
Audio files:
interstellar_theme.mp3: Background music.
thrust_sound_space.wav: Thruster sound.
celebration_sound.wav: Win sound.
buzzer_sound.wav: Crash sound.
alert_sound.wav: Asteroid proximity alert.





Place assets in the same directory as the script or handle missing assets with fallback rendering.
Installation

Clone the repository:git clone <repository-url>
cd <repository-directory>


Install Pygame:pip install pygame


Add optional asset files to the project directory.
Run the game:python mars_rover_landing.py



How to Play

Objective: Land the rover on the landing pad (marked with a red 'X') with low velocity and within the pad's boundaries.
Controls:
Left Arrow: Thrust left.
Right Arrow: Thrust right.
Up Arrow: Thrust forward.
Down Arrow: Thrust backward.
Spacebar: Thrust upward (counter gravity).
F11: Toggle fullscreen.
R: Restart after a successful landing.


Game Mechanics:
Start at 20,000 meters altitude with 1200 units of fuel.
Manage fuel consumption (1 unit per thrust, 2 for upward thrust).
Avoid asteroids; proximity warnings appear when close (<200m).
Land with velocity |vx| < 2, |vy| < 2, |vz| < 5 m/s, and position within the 50x50m landing pad.


Success: Triggers an animated sequence of an astronaut exiting the lander, followed by a win screen with moving orbs.
Failure: Crashing into asteroids or landing with high velocity/off-target triggers a restart after 2 seconds.

Technical Details

Rendering: Uses perspective projection with a focal length of 400 pixels for 3D effects.
Physics: Simulates gravity (-0.1 m/s²), thrust (0.5 m/s²), and velocity updates scaled by 0.1 for smooth gameplay.
Asteroids: 2000 asteroids with random positions, sizes (100-200 units), and colors, cached for performance.
Audio: Volume settings for thruster (0.9), win (0.8), lose (0.8), music (0.1), and alerts (0.8).
Performance: Runs at 60 FPS with a background image cache to optimize scaling.

Known Issues

Missing assets (images/audio) trigger fallbacks (drawn shapes or silence) with console warnings.
Fullscreen toggle may require re-rendering of background assets.
Large asteroid counts may impact performance on low-end systems.

Contributing
Feel free to fork the repository, submit issues, or create pull requests for enhancements. Suggestions for new features (e.g., additional obstacles, improved graphics) are welcome!
License
This project is licensed under the MIT License. See the LICENSE file for details.
