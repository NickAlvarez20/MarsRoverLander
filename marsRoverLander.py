import pygame
import sys
import random
import math
import traceback

pygame.init()
pygame.mixer.init()

width, height = 800, 600
screen = pygame.display.set_mode((width, height))
width, height = screen.get_size()  # Update in case of discrepancy
pygame.display.set_caption("Mars 3D Rover Landing Game")
clock = pygame.time.Clock()

# Constants
focal_length = 400  # Focal length for perspective projection
pad_size = 50  # Size of the landing pad
atmosphere_start = 10000  # Altitude where atmosphere entry begins
background_image_altitude = 5000  # Altitude to switch to background image
gravity = -0.1  # Gravity acceleration (negative towards surface)
thrust_power = 0.5  # Power of each thrust
fuel_consumption = 1  # Fuel used per thrust action
max_fuel = 1200  # Maximum fuel
initial_z = 20000  # Starting altitude
warning_threshold = 200  # Distance threshold for asteroid warning
alert_duration = 2000  # Alert sound duration in milliseconds (2 seconds)
min_scale = 10  # Minimum asteroid image scale
max_scale = 200  # Maximum asteroid image scale
zoom_stop_altitude = 500  # Altitude to stop background zoom

# Audio volume settings (0.0 to 1.0)
THRUST_VOLUME = 0.9  # Volume for thruster sound
WIN_VOLUME = 0.8  # Volume for win sound
LOSE_VOLUME = 0.8  # Volume for lose sound
MUSIC_VOLUME = 0.1  # Volume for background music
ALERT_VOLUME = 0.8  # Volume for alert sound

# Landing pad vertices for base polygon (at z=0)
pad_vertices = [
    [-pad_size/2, -pad_size/2, 0],
    [pad_size/2, -pad_size/2, 0],
    [pad_size/2, pad_size/2, 0],
    [-pad_size/2, pad_size/2, 0]
]

# Inner square for detail (80% of pad_size, at z=0)
inner_pad_size = pad_size * 0.8
inner_pad_vertices = [
    [-inner_pad_size/2, -inner_pad_size/2, 0],
    [inner_pad_size/2, -inner_pad_size/2, 0],
    [inner_pad_size/2, inner_pad_size/2, 0],
    [-inner_pad_size/2, inner_pad_size/2, 0]
]

# Raised edge vertices (at z=2 for 3D effect)
edge_height = 2
edge_vertices = [
    ([-pad_size/2, -pad_size/2, 0], [-pad_size/2, -pad_size/2, edge_height]),
    ([pad_size/2, -pad_size/2, 0], [pad_size/2, -pad_size/2, edge_height]),
    ([-pad_size/2, pad_size/2, 0], [-pad_size/2, pad_size/2, edge_height]),
    ([pad_size/2, pad_size/2, 0], [pad_size/2, pad_size/2, edge_height]),
    ([-pad_size/2, -pad_size/2, 0], [-pad_size/2, pad_size/2, 0]),
    ([-pad_size/2, -pad_size/2, edge_height], [-pad_size/2, pad_size/2, edge_height]),
    ([pad_size/2, -pad_size/2, 0], [pad_size/2, pad_size/2, 0]),
    ([pad_size/2, -pad_size/2, edge_height], [pad_size/2, pad_size/2, edge_height])
]

# Red 'X' vertices for the landing pad (diagonal lines, at z=0)
x_vertices = [
    ([-pad_size/2, -pad_size/2, 0], [pad_size/2, pad_size/2, 0]),  # Diagonal 1
    ([-pad_size/2, pad_size/2, 0], [pad_size/2, -pad_size/2, 0])   # Diagonal 2
]

# Grid lines for texture (at z=0)
grid_spacing = pad_size / 4
grid_lines = []
for i in range(-1, 2):  # 3 lines each way
    x = i * grid_spacing
    y = i * grid_spacing
    grid_lines.append(([-pad_size/2, y, 0], [pad_size/2, y, 0]))  # Horizontal
    grid_lines.append(([x, -pad_size/2, 0], [x, pad_size/2, 0]))  # Vertical

# Central target circle (at z=0)
target_radius = pad_size / 10

# Generate random asteroids with unique properties
asteroids = []
for _ in range(2000):  # 1000 asteroids
    base_size = random.uniform(100, 200)  # Larger base size range for challenge
    color = (random.randint(450, 750), random.randint(100, 150), random.randint(100, 150), 255)  # Grey colors
    offsets = [(random.uniform(-base_size/1.5, base_size/1.5), random.uniform(-base_size/1.5, base_size/1.5), random.uniform(1, 1.5)) for _ in range(10)]  # 4 sub-circles
    asteroids.append({
        'pos': [random.uniform(-4000, 4000), random.uniform(-4000, 4000), random.uniform(4000, 24000)],  # Tighter x/y and z range
        'size': base_size,
        'color': color,
        'offsets': offsets,
        'radius': base_size  # For collision detection
    })

# Load and pre-scale asteroid image
try:
    asteroid_image = pygame.image.load('asteroid.png').convert_alpha()
    # Create a cache of pre-scaled images
    asteroid_image_cache = {}
    for size in range(min_scale, max_scale + 1, 10):  # Cache sizes in steps of 10
        asteroid_image_cache[size] = pygame.transform.scale(asteroid_image, (size, size))
except pygame.error as e:
    print(f"Warning: Could not load asteroid image: {e}")
    traceback.print_exc()
    asteroid_image = None
    asteroid_image_cache = None

# Load background image
background_image = None
try:
    background_image = pygame.image.load('mars_background.jpg')
    try:
        background_image = background_image.convert()
    except:
        print("Warning: Could not convert background image, using original.")
        traceback.print_exc()
except pygame.error as e:
    print(f"Error: Could not load background image 'mars_background.jpg': {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Unexpected error loading background image: {e}")
    traceback.print_exc()

# Load intro image (replace 'intro_image.jpg' with your JPG or PNG file path)
intro_image = None
try:
    intro_image = pygame.image.load('intro_image.jpg').convert_alpha()
except pygame.error as e:
    print(f"Error: Could not load intro image: {e}")
    traceback.print_exc()

# Background cache variables
last_zoom_factor = None
last_scaled_background = None
last_scaled_w = None
last_scaled_h = None

# Function to project a 3D point to 2D screen coordinates
def project(point, cam_x, cam_y, cam_z):
    dx = point[0] - cam_x
    dy = point[1] - cam_y
    dz = point[2] - cam_z  # Relative z (surface at z=0, camera at positive z)
    if dz >= 0 or abs(dz) < 0.1:  # Point behind, at camera, or too close
        return None
    px = (dx * focal_length / -dz) + width / 2
    py = (dy * focal_length / -dz) + height / 2
    return (px, py)

# Function to get background color based on altitude
def get_bg_color(cam_z):
    if cam_z > atmosphere_start:
        return (0, 0, 0)  # Black in space
    else:
        t = (atmosphere_start - cam_z) / (atmosphere_start - background_image_altitude)  # Transition to image
        t = max(0, min(1, t))  # Clamp t to [0, 1]
        r = int(200 * t)  # Dusty red (200, 100, 50)
        g = int(100 * t)
        b = int(50 * t)
        return (r, g, b)

# Restart function to reset game state
def restart():
    global cam_x, cam_y, cam_z, vx, vy, vz, fuel, is_thrusting, is_alerting, last_alert_time, last_scaled_background, last_zoom_factor
    cam_x = random.uniform(-200, 200)  # Starting offset
    cam_y = random.uniform(-200, 200)
    cam_z = initial_z
    vx = random.uniform(-5, 5)  # Initial velocities
    vy = random.uniform(-5, 5)
    vz = -10  # Initial downward velocity
    fuel = max_fuel
    is_thrusting = False
    is_alerting = False
    last_alert_time = 0  # Reset alert timer
    last_scaled_background = None
    last_zoom_factor = None
    try:
        pygame.mixer.music.load('interstellar_theme.mp3')
        pygame.mixer.music.set_volume(MUSIC_VOLUME)  # Set background music volume
        pygame.mixer.music.play(-1)
    except pygame.error as e:
        print(f"Warning: Could not load background music: {e}")
        traceback.print_exc()

# Font for HUD and messages
font = pygame.font.SysFont(None, 30)
large_font = pygame.font.SysFont(None, 50)

# Pre-render warning texts
warning_surfaces = {
    "LEFT": font.render("Warning: Thrust LEFT!", True, (255, 0, 0)),
    "RIGHT": font.render("Warning: Thrust RIGHT!", True, (255, 0, 0)),
    "UP": font.render("Warning: Thrust UP!", True, (255, 0, 0)),
    "DOWN": font.render("Warning: Thrust DOWN!", True, (255, 0, 0))
}

# Load audio files with error handling
try:
    thrust_sound = pygame.mixer.Sound('thrust_sound_space.wav')
    thrust_sound.set_volume(THRUST_VOLUME)  # Set thruster sound volume
except pygame.error as e:
    print(f"Warning: Could not load thrust sound: {e}")
    traceback.print_exc()
    thrust_sound = None

try:
    win_sound = pygame.mixer.Sound('celebration_sound.wav')
    win_sound.set_volume(WIN_VOLUME)  # Set win sound volume
except pygame.error as e:
    print(f"Warning: Could not load win sound: {e}")
    traceback.print_exc()
    win_sound = None

try:
    lose_sound = pygame.mixer.Sound('buzzer_sound.wav')
    lose_sound.set_volume(LOSE_VOLUME)  # Set lose sound volume
except pygame.error as e:
    print(f"Warning: Could not load lose sound: {e}")
    traceback.print_exc()
    lose_sound = None

try:
    alert_sound = pygame.mixer.Sound('alert_sound.wav')
    alert_sound.set_volume(ALERT_VOLUME)  # Set alert sound volume
except pygame.error as e:
    print(f"Warning: Could not load alert sound: {e}")
    traceback.print_exc()
    alert_sound = None

# Intro animation (replaced with fading background image)
def play_intro():
    global screen, width, height, last_scaled_background, last_zoom_factor
    if intro_image is None:
        # Fallback if image not loaded: skip intro or use black screen
        pygame.time.wait(1000)  # Wait 1 second
        return
    animation_frames = 180  # ~3 seconds at 60 fps
    frame = 0
    intro_running = True
    while intro_running and frame < animation_frames:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:  # Toggle fullscreen during intro
                    global fullscreen
                    fullscreen = not fullscreen
                    screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN if fullscreen else 0)
                    width, height = screen.get_size()  # Update width and height
                    last_scaled_background = None
                    last_zoom_factor = None
                else:
                    intro_running = False  # Skip on any other key press
        # Calculate alpha for fade in/out
        if frame < 90:
            alpha = int(255 * (frame / 90))  # Fade in
        else:
            alpha = int(255 * ((animation_frames - frame) / 90))  # Fade out
        # Draw
        screen.fill((0, 0, 0))  # Black background
        # Scale intro image to current screen size
        scaled_intro = pygame.transform.scale(intro_image, (width, height))
        temp_surface = pygame.Surface(scaled_intro.get_size(), pygame.SRCALPHA)
        temp_surface.blit(scaled_intro, (0, 0))
        temp_surface.set_alpha(alpha)
        screen.blit(temp_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        frame += 1

# Initial game state
last_alert_time = 0  # Initialize alert timer
fullscreen = False  # Track fullscreen state
restart()

# Play intro animation
play_intro()

running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            fullscreen = not fullscreen
            screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN if fullscreen else 0)
            width, height = screen.get_size()  # Update width and height
            last_scaled_background = None
            last_zoom_factor = None

    # Fill background based on altitude
    screen.fill(get_bg_color(cam_z))
    if cam_z <= background_image_altitude and background_image:
        try:
            # Calculate zoom factor, stopping at 500m
            zoom_altitude = max(cam_z, zoom_stop_altitude)
            zoom_factor = background_image_altitude / max(zoom_altitude, 1)
            if last_zoom_factor == zoom_factor and last_scaled_background is not None:
                scaled_background = last_scaled_background
                scaled_w = last_scaled_w
                scaled_h = last_scaled_h
            else:
                orig_w, orig_h = background_image.get_size()
                center_x = orig_w / 2.0
                center_y = orig_h / 2.0
                half_vis_w = (width / 2.0) / zoom_factor
                half_vis_h = (height / 2.0) / zoom_factor
                ideal_left = center_x - half_vis_w
                ideal_right = center_x + half_vis_w
                ideal_top = center_y - half_vis_h
                ideal_bottom = center_y + half_vis_h
                left = max(0, ideal_left)
                top = max(0, ideal_top)
                right = min(orig_w, ideal_right)
                bottom = min(orig_h, ideal_bottom)
                crop_w = max(0, right - left)
                crop_h = max(0, bottom - top)
                if crop_w > 0 and crop_h > 0:
                    crop_rect = pygame.Rect(left, top, crop_w, crop_h)
                    cropped = background_image.subsurface(crop_rect)
                    scaled_w = int(crop_w * zoom_factor)
                    scaled_h = int(crop_h * zoom_factor)
                    scaled_background = pygame.transform.scale(cropped, (scaled_w, scaled_h))
                    last_scaled_background = scaled_background
                    last_scaled_w = scaled_w
                    last_scaled_h = scaled_h
                    last_zoom_factor = zoom_factor
                else:
                    # No visible crop, skip blit
                    continue
            # Center the scaled image
            blit_x = (width - scaled_w) // 2
            blit_y = (height - scaled_h) // 2
            screen.blit(scaled_background, (blit_x, blit_y))
        except pygame.error as e:
            print(f"Warning: Could not render background image: {e}")
            traceback.print_exc()

    # Draw asteroids and check collisions/warnings
    closest_ast = None
    min_dist = float('inf')
    collided = False
    for ast in asteroids:
        p = project(ast['pos'], cam_x, cam_y, cam_z)
        # Check collision
        dist = math.sqrt((cam_x - ast['pos'][0])**2 + (cam_y - ast['pos'][1])**2 + (cam_z - ast['pos'][2])**2)
        if dist < ast['radius'] + 10:  # Assume rover radius ~10
            # Crash on asteroid
            pygame.mixer.music.stop()
            if thrust_sound:
                thrust_sound.stop()
            if alert_sound:
                alert_sound.stop()
            if lose_sound:
                lose_sound.play()
            screen.fill((255, 0, 0))
            screen.blit(large_font.render("Crash! Restarting...", True, (0, 0, 0)), (width / 2 - 200, height / 2))
            pygame.display.flip()
            pygame.time.wait(2000)
            restart()
            collided = True
            break  # Exit loop after crash
        # Update closest asteroid for warning
        if dist < min_dist:
            min_dist = dist
            closest_ast = ast
        # Draw asteroid
        if p:
            if asteroid_image_cache:
                # Use pre-scaled image
                dz = ast['pos'][2] - cam_z
                scale = max(min(int(focal_length / -dz * ast['size'] * 2), max_scale), min_scale)
                scale = (scale // 10) * 10  # Snap to nearest cached size
                scaled_image = asteroid_image_cache.get(scale, asteroid_image_cache[min_scale])
                screen.blit(scaled_image, (int(p[0] - scale / 2), int(p[1] - scale / 2)))
            else:
                # Fallback to drawn circles
                for offset in ast['offsets']:
                    offset_x, offset_y, scale = offset
                    size = ast['size'] * scale
                    pygame.draw.circle(screen, ast['color'], (int(p[0] + offset_x), int(p[1] + offset_y)), int(size))

    if collided:
        continue  # Skip rest of loop after crash

    # Draw landing pad
    projected = [project(v, cam_x, cam_y, cam_z) for v in pad_vertices]
    if all(p is not None for p in projected):  # Check if all projections are valid
        # Draw base polygon (darker grey for shadow)
        pygame.draw.polygon(screen, (100, 100, 100), [(int(px), int(py)) for (px, py) in projected], 0)
        # Draw inner polygon (lighter grey for top surface)
        inner_projected = [project(v, cam_x, cam_y, cam_z) for v in inner_pad_vertices]
        if all(p is not None for p in inner_projected):
            pygame.draw.polygon(screen, (150, 150, 150), [(int(px), int(py)) for (px, py) in inner_projected], 0)
        # Draw grid lines for texture
        for (start, end) in grid_lines:
            p1 = project(start, cam_x, cam_y, cam_z)
            p2 = project(end, cam_x, cam_y, cam_z)
            if p1 and p2:
                pygame.draw.line(screen, (180, 180, 180), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 1)
        # Draw central target circle
        center_p = project([0, 0, 0], cam_x, cam_y, cam_z)
        if center_p:
            target_scale = focal_length / max(-cam_z, 1) * target_radius  # Avoid division by zero
            pygame.draw.circle(screen, (200, 200, 200), (int(center_p[0]), int(center_p[1])), max(int(target_scale), 2), 2)
        # Draw raised edges (at z=2)
        for (start, end) in edge_vertices:
            p1 = project(start, cam_x, cam_y, cam_z)
            p2 = project(end, cam_x, cam_y, cam_z)
            if p1 and p2:
                pygame.draw.line(screen, (120, 120, 120), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 3)
        # Draw red 'X' on top
        for (start, end) in x_vertices:
            p1 = project(start, cam_x, cam_y, cam_z)
            p2 = project(end, cam_x, cam_y, cam_z)
            if p1 and p2:
                pygame.draw.line(screen, (255, 0, 0), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 3)

    # Calculate projected center of pad for HUD arrows (use z=0 for alignment with hitbox)
    center_p = project([0, 0, 0], cam_x, cam_y, cam_z)
    if center_p:
        dx = center_p[0] - width / 2
        dy = center_p[1] - height / 2
        # Draw directional arrows if off-center
        if abs(dx) > 10 or abs(dy) > 10:
            if dx < -10:  # Pad to the left, thrust left
                screen.blit(font.render("<", True, (255, 0, 0)), (width / 2 - 50, height / 2))
            if dx > 10:  # Pad to the right, thrust right
                screen.blit(font.render(">", True, (255, 0, 0)), (width / 2 + 50, height / 2))
            if dy < -10:  # Pad up, thrust up
                screen.blit(font.render("^", True, (255, 0, 0)), (width / 2, height / 2 - 50))
            if dy > 10:  # Pad down, thrust down
                screen.blit(font.render("v", True, (255, 0, 0)), (width / 2, height / 2 + 50))

    # HUD: Altitude, Fuel gauge, Velocity, Speed
    screen.blit(font.render(f"Altitude: {int(cam_z)} m", True, (255, 255, 255)), (10, 10))
    # Fuel gauge
    pygame.draw.rect(screen, (255, 0, 0), (10, 40, 200, 20))  # Background
    pygame.draw.rect(screen, (0, 255, 0), (10, 40, 200 * (fuel / max_fuel), 20))  # Fuel bar
    screen.blit(font.render(f"Fuel: {int(fuel)}", True, (255, 255, 255)), (10, 65))
    # Velocity info
    screen.blit(font.render(f"Velocity: X={int(vx)} Y={int(vy)} Z={int(vz)} m/s", True, (255, 255, 255)), (10, 90))
    # Speed (magnitude of velocity vector)
    speed = math.sqrt(vx**2 + vy**2 + vz**2)
    screen.blit(font.render(f"Speed: {int(speed)} m/s", True, (255, 255, 255)), (10, 115))

    # Asteroid warning system
    current_time = pygame.time.get_ticks()
    current_alert = min_dist < warning_threshold and closest_ast is not None
    if current_alert:
        dx = closest_ast['pos'][0] - cam_x
        dy = closest_ast['pos'][1] - cam_y
        # Determine dominant direction to thrust away
        direction = ""
        if abs(dx) > abs(dy):
            if dx > 0:
                direction = "LEFT"  # Asteroid right, thrust left
            else:
                direction = "RIGHT"  # Asteroid left, thrust right
        else:
            if dy > 0:
                direction = "UP"  # Asteroid down, thrust up (negative y)
            else:
                direction = "DOWN"  # Asteroid up, thrust down (positive y)
        # Blit pre-rendered warning
        screen.blit(warning_surfaces[direction], (width // 2 - warning_surfaces[direction].get_width() // 2, height // 2 - warning_surfaces[direction].get_height() // 2))
        # Play alert sound if not already playing or if 2 seconds have passed
        if not is_alerting and alert_sound and (current_time - last_alert_time >= alert_duration):
            alert_sound.play()
            last_alert_time = current_time
            is_alerting = True
    else:
        # Stop alert sound if condition no longer met
        if is_alerting and alert_sound:
            alert_sound.stop()
            is_alerting = False
    # Stop alert sound after 2 seconds
    if is_alerting and alert_sound and (current_time - last_alert_time >= alert_duration):
        alert_sound.stop()
        is_alerting = False

    # Controls: Thrust (use fuel if available)
    keys = pygame.key.get_pressed()
    thrust_x = 0
    thrust_y = 0
    thrust_z = 0
    current_thrusting = False
    if fuel > 0:
        if keys[pygame.K_LEFT]:
            thrust_x = -thrust_power
            fuel -= fuel_consumption
            current_thrusting = True
        if keys[pygame.K_RIGHT]:
            thrust_x = thrust_power
            fuel -= fuel_consumption
            current_thrusting = True
        if keys[pygame.K_UP]:
            thrust_y = -thrust_power  # Forward (negative y, assuming orientation)
            fuel -= fuel_consumption
            current_thrusting = True
        if keys[pygame.K_DOWN]:
            thrust_y = thrust_power  # Backward
            fuel -= fuel_consumption
            current_thrusting = True
        if keys[pygame.K_SPACE]:  # Main upward thrust to counter gravity
            thrust_z = thrust_power * 2  # Stronger for vertical
            fuel -= fuel_consumption * 2
            current_thrusting = True

    if fuel < 0:
        fuel = 0

    # Manage thrust sound
    if current_thrusting and not is_thrusting and thrust_sound:
        thrust_sound.play(-1)
    if not current_thrusting and is_thrusting and thrust_sound:
        thrust_sound.stop()
    is_thrusting = current_thrusting

    # Physics update
    vz += gravity  # Apply gravity
    vx += thrust_x
    vy += thrust_y
    vz += thrust_z
    cam_x += vx * 0.1  # Scale movement for simulation
    cam_y += vy * 0.1
    cam_z += vz * 0.1

    # Check for landing or crash
    if cam_z <= 0:
        if abs(vx) < 2 and abs(vy) < 2 and abs(vz) < 5 and abs(cam_x) < pad_size / 2 and abs(cam_y) < pad_size / 2:
            # Successful landing
            pygame.mixer.music.stop()
            if thrust_sound:
                thrust_sound.stop()
            if alert_sound:
                alert_sound.stop()
            if win_sound:
                win_sound.play()
            # Ensure display is updated before starting animation
            pygame.display.flip()
            # First scene: Astronaut exiting lander
            animation_frames = 120  # ~4 seconds at 30 fps
            pivot_x = width / 2 + 50
            pivot_y = height - 100
            door_length = 40
            astronaut_x = width / 2 + 30
            astronaut_y = height - 100
            anim_running = True
            frame = 0
            while anim_running and frame < animation_frames:
                # Process events to prevent freezing
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        anim_running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            fullscreen = not fullscreen
                            # Reinitialize display with current mode
                            screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN if fullscreen else 0)
                            width, height = screen.get_size()  # Update width and height
                            last_scaled_background = None
                            last_zoom_factor = None
                            # Ensure screen is cleared after mode switch
                            screen.fill((200, 100, 50))
                            pygame.display.flip()
                if not anim_running:
                    break
                # Draw animation
                screen.fill((200, 100, 50))  # Mars surface
                # Draw lander body
                lander_rect = pygame.Rect(width / 2 - 50, height - 200, 100, 150)
                pygame.draw.rect(screen, (150, 150, 150), lander_rect)
                # Draw hatch door
                if frame < 60:
                    angle = 90 - (frame / 60 * 90)  # from 90 (vertical) to 0 (horizontal)
                else:
                    angle = 0
                end_x = pivot_x + door_length * math.cos(math.radians(angle))
                end_y = pivot_y + door_length * math.sin(math.radians(angle))
                pygame.draw.line(screen, (100, 100, 100), (pivot_x, pivot_y), (end_x, end_y), 5)
                # Draw astronaut if hatch is open enough (frame > 60)
                if frame > 60:
                    move_frame = frame - 60
                    astronaut_x += 1  # Move right 1 pixel per frame
                    # Draw helmet
                    pygame.draw.circle(screen, (200, 200, 200), (int(astronaut_x), int(astronaut_y - 30)), 15)
                    # Draw visor: black upside-down filled U
                    visor_color = (0, 0, 0)
                    visor_center = (int(astronaut_x), int(astronaut_y - 28))
                    visor_radius = 10
                    points = [(visor_center[0], visor_center[1])]
                    for angle in range(180, 361, 10):
                        x = visor_center[0] + visor_radius * math.cos(math.radians(angle))
                        y = visor_center[1] + visor_radius * math.sin(math.radians(angle))
                        points.append((x, y))
                    pygame.draw.polygon(screen, visor_color, points)
                    # Draw suit body
                    pygame.draw.rect(screen, (200, 200, 200), (astronaut_x - 15, astronaut_y - 15, 30, 40))
                    # Draw arms
                    arm_y = astronaut_y - 5
                    pygame.draw.rect(screen, (200, 200, 200), (astronaut_x - 25, arm_y - 5, 10, 20))
                    pygame.draw.rect(screen, (200, 200, 200), (astronaut_x + 15, arm_y - 5, 10, 20))
                    # Draw legs with simple walking animation
                    leg_offset = math.sin(move_frame * 0.5) * 5
                    pygame.draw.rect(screen, (200, 200, 200), (astronaut_x - 10, astronaut_y + 25, 8, 20 + leg_offset))
                    pygame.draw.rect(screen, (200, 200, 200), (astronaut_x + 2, astronaut_y + 25, 8, 20 - leg_offset))
                # Force display update
                pygame.display.flip()
                clock.tick(30)
                frame += 1
            if not running:
                break
            # Second scene: Animated win screen with moving orbs
            orbs = []
            for _ in range(50):
                orb = {
                    'x': random.randint(0, width),
                    'y': random.randint(0, height),
                    'vx': random.uniform(-2, 2),
                    'vy': random.uniform(-2, 2),
                    'color': (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
                    'radius': random.randint(5, 15)
                }
                orbs.append(orb)
            waiting = True
            while waiting:
                # Process events to prevent freezing
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        waiting = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            fullscreen = not fullscreen
                            screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN if fullscreen else 0)
                            width, height = screen.get_size()  # Update width and height
                            last_scaled_background = None
                            last_zoom_factor = None
                            # Ensure screen is cleared after mode switch
                            screen.fill((0, 255, 0))
                            pygame.display.flip()
                        elif event.key == pygame.K_r:
                            restart()
                            waiting = False
                if not waiting:
                    break
                # Update orbs
                for orb in orbs:
                    orb['x'] += orb['vx']
                    orb['y'] += orb['vy']
                    if orb['x'] < orb['radius'] or orb['x'] > width - orb['radius']:
                        orb['vx'] *= -1
                    if orb['y'] < orb['radius'] or orb['y'] > height - orb['radius']:
                        orb['vy'] *= -1
                # Draw
                screen.fill((0, 255, 0))
                screen.blit(large_font.render("You Landed!", True, (0, 0, 0)), (width / 2 - 150, height / 2 - 50))
                screen.blit(font.render("Press R to restart from the top", True, (0, 0, 0)), (width / 2 - 150, height / 2 + 10))
                for orb in orbs:
                    pygame.draw.circle(screen, orb['color'], (int(orb['x']), int(orb['y'])), orb['radius'])
                # Force display update
                pygame.display.flip()
                clock.tick(60)
        else:
            # Crash
            pygame.mixer.music.stop()
            if thrust_sound:
                thrust_sound.stop()
            if alert_sound:
                alert_sound.stop()
            if lose_sound:
                lose_sound.play()
            screen.fill((255, 0, 0))
            screen.blit(large_font.render("Crash! Restarting...", True, (0, 0, 0)), (width / 2 - 200, height / 2))
            pygame.display.flip()
            pygame.time.wait(2000)
            restart()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()