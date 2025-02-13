import pygame
import sys
import random

# ----- Pygame Setup -----
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Highway Dodge")
clock = pygame.time.Clock()

# ----- Road (Highway) Parameters -----
# We draw a perspective road as a trapezoid.
horizon_y = SCREEN_HEIGHT * 0.3  # vanishing point (top of the road)
# Top edge (narrow at horizon)
left_top = SCREEN_WIDTH * 0.45
right_top = SCREEN_WIDTH * 0.55
# Bottom edge (wide at bottom)
left_bottom = SCREEN_WIDTH * 0.2
right_bottom = SCREEN_WIDTH * 0.8

# How many lanes?
num_lanes = 3

def get_road_boundaries(y):
    """
    For a given screen y-coordinate (between horizon_y and bottom),
    interpolate the left and right boundaries of the road.
    """
    t = (y - horizon_y) / (SCREEN_HEIGHT - horizon_y)
    left = left_top + t * (left_bottom - left_top)
    right = right_top + t * (right_bottom - right_top)
    return left, right

def get_lane_center(lane, y):
    """
    For a given lane (0 to num_lanes-1) and a y value,
    compute the center x-coordinate of that lane.
    """
    left, right = get_road_boundaries(y)
    lane_width = (right - left) / num_lanes
    center = left + lane_width * (lane + 0.5)
    return center

# ----- Player Car Settings -----
player_lane = 1  # start in the center lane (0-indexed)
base_car_width = 40
base_car_height = 80
# The player's car is drawn at the bottom of the screen.
def get_player_rect():
    bottom_offset = 10
    center_x = get_lane_center(player_lane, SCREEN_HEIGHT)
    car_width = base_car_width
    car_height = base_car_height
    rect = pygame.Rect(0, 0, car_width, car_height)
    rect.centerx = int(center_x)
    rect.bottom = SCREEN_HEIGHT - bottom_offset
    return rect

# ----- Road Speed & Controls -----
# Our “camera” moves down the road.
player_speed = 300  # initial speed (affects obstacle movement)
min_speed = 150
max_speed = 600
player_acceleration = 100   # speed increases when holding UP
player_brake = 150          # deceleration when holding DOWN

# ----- Obstacle (Other Car) Settings -----
# We'll simulate oncoming cars by having them “approach” from far away.
# We use a simple "z" coordinate where z=1000 spawns a car at the horizon
# and z=0 means the car has reached your position.
z_max = 1000.0
collision_threshold = 150  # when an obstacle gets below this z, collision is possible
# Each obstacle is a dict: {"lane": int, "z": float}
obstacles = []

def project_z_to_y(z):
    """
    Project a z-value (distance from you) to a screen y-coordinate.
    When z == z_max, the car is at the horizon.
    When z == 0, the car is at the bottom.
    """
    t = 1 - (z / z_max)  # t goes from 0 at horizon to 1 at bottom
    y = horizon_y + t * (SCREEN_HEIGHT - horizon_y)
    return y

def scale_from_z(z):
    """
    Compute a scale factor (for size) from the z-distance.
    At the horizon the car appears small; at the bottom, its full size.
    """
    min_scale = 0.3
    t = 1 - (z / z_max)
    scale = min_scale + t * (1 - min_scale)
    return scale

# ----- Obstacle Spawning -----
spawn_timer = 0
spawn_interval = 1.5  # seconds between spawns

# ----- Game State & Score -----
score = 0
game_over = False

# ----- Main Game Loop -----
while True:
    dt = clock.tick(60) / 1000.0  # delta time in seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Process key presses for lane change (only when game is not over)
        if event.type == pygame.KEYDOWN:
            if not game_over:
                if event.key == pygame.K_LEFT and player_lane > 0:
                    player_lane -= 1
                elif event.key == pygame.K_RIGHT and player_lane < num_lanes - 1:
                    player_lane += 1
            # If game over, press R to restart
            if event.key == pygame.K_r and game_over:
                obstacles = []
                score = 0
                player_speed = 300
                player_lane = 1
                spawn_timer = 0
                game_over = False

    # Continuous key presses: accelerate/brake (when playing)
    keys = pygame.key.get_pressed()
    if not game_over:
        if keys[pygame.K_UP]:
            player_speed += player_acceleration * dt
            if player_speed > max_speed:
                player_speed = max_speed
        if keys[pygame.K_DOWN]:
            player_speed -= player_brake * dt
            if player_speed < min_speed:
                player_speed = min_speed

    if not game_over:
        # ----- Spawn Obstacles -----
        spawn_timer -= dt
        if spawn_timer <= 0:
            spawn_timer = spawn_interval
            new_lane = random.randint(0, num_lanes - 1)
            obstacles.append({"lane": new_lane, "z": z_max})

        # ----- Update Obstacles -----
        # Move obstacles toward the player by decreasing z
        for obs in obstacles:
            obs["z"] -= player_speed * dt

        # Remove obstacles that have passed (z < 0) and add to score
        new_obs = []
        for obs in obstacles:
            if obs["z"] < 0:
                score += 10
            else:
                new_obs.append(obs)
        obstacles = new_obs

        # ----- Collision Detection -----
        player_rect = get_player_rect()
        for obs in obstacles:
            # Only check obstacles in the same lane and that are close
            if obs["lane"] == player_lane and obs["z"] < collision_threshold:
                y = project_z_to_y(obs["z"])
                scale = scale_from_z(obs["z"])
                car_width = base_car_width * scale
                car_height = base_car_height * scale
                center_x = get_lane_center(obs["lane"], y)
                obs_rect = pygame.Rect(0, 0, car_width, car_height)
                obs_rect.centerx = int(center_x)
                obs_rect.bottom = int(y)
                if player_rect.colliderect(obs_rect):
                    game_over = True
                    break

    # ----- Drawing -----
    # Fill background (grass)
    screen.fill((0, 150, 0))

    # Draw the road as a trapezoid
    road_polygon = [
        (left_top, horizon_y),
        (right_top, horizon_y),
        (right_bottom, SCREEN_HEIGHT),
        (left_bottom, SCREEN_HEIGHT)
    ]
    pygame.draw.polygon(screen, (50, 50, 50), road_polygon)
    # Draw road boundaries
    pygame.draw.line(screen, (255, 255, 255), (left_top, horizon_y), (left_bottom, SCREEN_HEIGHT), 3)
    pygame.draw.line(screen, (255, 255, 255), (right_top, horizon_y), (right_bottom, SCREEN_HEIGHT), 3)

    # Draw dashed lane dividers
    num_dashes = 20
    for lane in range(1, num_lanes):
        for i in range(num_dashes):
            t1 = i / num_dashes
            t2 = (i + 0.5) / num_dashes
            y1 = horizon_y + t1 * (SCREEN_HEIGHT - horizon_y)
            y2 = horizon_y + t2 * (SCREEN_HEIGHT - horizon_y)
            left1, right1 = get_road_boundaries(y1)
            left2, right2 = get_road_boundaries(y2)
            divider_x1 = left1 + (right1 - left1) * (lane / num_lanes)
            divider_x2 = left2 + (right2 - left2) * (lane / num_lanes)
            pygame.draw.line(screen, (255, 255, 255), (divider_x1, y1), (divider_x2, y2), 2)

    # Draw the player's car (blue rectangle)
    player_rect = get_player_rect()
    pygame.draw.rect(screen, (0, 0, 255), player_rect)

    # Draw obstacles (red cars)
    for obs in obstacles:
        y = project_z_to_y(obs["z"])
        scale = scale_from_z(obs["z"])
        car_width = base_car_width * scale
        car_height = base_car_height * scale
        center_x = get_lane_center(obs["lane"], y)
        obs_rect = pygame.Rect(0, 0, car_width, car_height)
        obs_rect.centerx = int(center_x)
        obs_rect.bottom = int(y)
        pygame.draw.rect(screen, (255, 0, 0), obs_rect)

    # Draw HUD: speed and score
    font = pygame.font.SysFont("Arial", 24)
    hud_text = font.render(f"Speed: {int(player_speed)}  Score: {score}", True, (255, 255, 255))
    screen.blit(hud_text, (10, 10))

    # Game over message
    if game_over:
        go_text = font.render("GAME OVER! Press R to restart", True, (255, 255, 0))
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(go_text, go_rect)

    pygame.display.flip()
