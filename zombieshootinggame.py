import pygame, math, random, sys

# --- Constants and Settings ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FOV = math.radians(60)
HALF_FOV = FOV / 2
MAX_DEPTH = 800  # maximum distance to cast rays
TILE_SIZE = 64  # size of one map cell
# Projection coefficient for wall slice height
PROJ_COEFF = (SCREEN_WIDTH / 2) / math.tan(HALF_FOV)

# Player settings
player_x = 100.0
player_y = 100.0
player_angle = 0.0
player_speed = 150   # movement speed (units/second)
turn_speed = math.radians(90)  # rotation speed (radians/sec)
player_health = 100
max_health = 100
player_ammo = 10
max_ammo = 10
score = 0

# A simple grid map (as a list of strings)
# "1" are walls, "0" are empty spaces.
world_map = [
    "111111111111",
    "100000000001",
    "101111110101",
    "101000010101",
    "101011010101",
    "101000010101",
    "101111110101",
    "100000000001",
    "111111111111"
]
MAP_ROWS = len(world_map)
MAP_COLS = len(world_map[0])

# --- Enemy (Zombie Stickman) Setup ---
# Each enemy is a dict with keys: "x", "y", "health"
enemies = []

def spawn_enemies(num):
    """Spawn a given number of enemies in open spaces away from the player."""
    global enemies
    enemies = []
    for _ in range(num):
        while True:
            ex = random.randint(1, MAP_COLS - 2) * TILE_SIZE + TILE_SIZE / 2
            ey = random.randint(1, MAP_ROWS - 2) * TILE_SIZE + TILE_SIZE / 2
            cell_x = int(ex // TILE_SIZE)
            cell_y = int(ey // TILE_SIZE)
            if world_map[cell_y][cell_x] == '0':
                # Avoid starting too close to the player
                if math.hypot(ex - player_x, ey - player_y) > 100:
                    enemies.append({"x": ex, "y": ey, "health": 3})
                    break

spawn_enemies(5)

# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Zombie FPS – Stickman Attack")
clock = pygame.time.Clock()

# Game states: "start", "playing", "game_over"
game_state = "start"

# --- Helper Functions ---

def draw_text(surface, text, size, color, center):
    """Draw centered text on a surface."""
    font = pygame.font.SysFont("Arial", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    surface.blit(text_surface, text_rect)

def cast_ray(px, py, angle):
    """
    Cast a ray from (px,py) at a given angle.
    Step along the ray until a wall cell ("1") is hit or MAX_DEPTH is reached.
    """
    sin_a = math.sin(angle)
    cos_a = math.cos(angle)
    distance = 0
    step = 1
    while distance < MAX_DEPTH:
        test_x = px + cos_a * distance
        test_y = py + sin_a * distance
        map_x = int(test_x // TILE_SIZE)
        map_y = int(test_y // TILE_SIZE)
        if map_x < 0 or map_x >= MAP_COLS or map_y < 0 or map_y >= MAP_ROWS:
            return distance
        if world_map[map_y][map_x] == '1':
            return distance
        distance += step
    return MAX_DEPTH

def draw_walls():
    """Render the 3D walls by casting a ray for each screen column."""
    for x in range(SCREEN_WIDTH):
        # Calculate the ray angle for this vertical slice
        ray_angle = player_angle - HALF_FOV + (x / SCREEN_WIDTH) * FOV
        distance = cast_ray(player_x, player_y, ray_angle)
        # Remove fish-eye distortion:
        distance *= math.cos(player_angle - ray_angle)
        if distance == 0:
            distance = 0.0001
        wall_height = (TILE_SIZE / distance) * PROJ_COEFF
        # Shading based on distance:
        shade = 255 / (1 + distance * distance * 0.0001)
        color = (shade, shade, shade)
        start_y = int(SCREEN_HEIGHT / 2 - wall_height / 2)
        end_y = int(SCREEN_HEIGHT / 2 + wall_height / 2)
        pygame.draw.line(screen, color, (x, start_y), (x, end_y))

def draw_enemy(enemy):
    """Project and draw a zombie stickman enemy in the 3D view."""
    # Get vector from player to enemy.
    dx = enemy["x"] - player_x
    dy = enemy["y"] - player_y
    distance = math.hypot(dx, dy)
    # Angle from player to enemy.
    enemy_angle = math.atan2(dy, dx)
    # Relative angle to player's view.
    delta_angle = enemy_angle - player_angle
    delta_angle = math.atan2(math.sin(delta_angle), math.cos(delta_angle))
    # Only draw if within the field-of-view.
    if abs(delta_angle) > HALF_FOV:
        return
    # Determine screen x-coordinate (projected)
    screen_x = (delta_angle / HALF_FOV) * (SCREEN_WIDTH / 2) + (SCREEN_WIDTH / 2)
    # Size scales with distance.
    enemy_size = int((TILE_SIZE / distance) * PROJ_COEFF)
    if enemy_size <= 0:
        return
    screen_y = SCREEN_HEIGHT // 2
    # --- Draw Stickman ---
    # Head as a circle.
    head_radius = enemy_size // 6
    head_center = (int(screen_x), int(screen_y - enemy_size // 2))
    pygame.draw.circle(screen, (0, 255, 0), head_center, head_radius, 1)
    # Body: vertical line.
    body_start = (int(screen_x), int(screen_y - enemy_size // 2 + head_radius))
    body_end = (int(screen_x), int(screen_y + enemy_size // 4))
    pygame.draw.line(screen, (0, 255, 0), body_start, body_end, 1)
    # Arms: horizontal line across the mid-body.
    body_mid_y = (body_start[1] + body_end[1]) // 2
    arm_span = enemy_size // 4
    pygame.draw.line(screen, (0, 255, 0),
                     (int(screen_x - arm_span), body_mid_y),
                     (int(screen_x + arm_span), body_mid_y), 1)
    # Legs: two diagonal lines.
    leg_length = enemy_size // 4
    pygame.draw.line(screen, (0, 255, 0), body_end,
                     (int(screen_x - arm_span), body_end[1] + leg_length), 1)
    pygame.draw.line(screen, (0, 255, 0), body_end,
                     (int(screen_x + arm_span), body_end[1] + leg_length), 1)

def update_enemies(dt):
    """Move each enemy toward the player and deal damage if too close."""
    global player_health, score
    for enemy in enemies:
        if enemy["health"] > 0:
            dx = player_x - enemy["x"]
            dy = player_y - enemy["y"]
            distance = math.hypot(dx, dy)
            if distance > 0:
                move_step = 50 * dt  # enemy speed
                enemy["x"] += (dx / distance) * move_step
                enemy["y"] += (dy / distance) * move_step
            # Attack the player if too near.
            if distance < 30:
                player_health -= 20 * dt  # damage per second
                if player_health < 0:
                    player_health = 0

def shoot():
    """Handle shooting – reduce ammo and damage the closest enemy in the crosshair."""
    global player_ammo, score
    if player_ammo <= 0:
        return
    player_ammo -= 1
    hit_enemy = None
    hit_distance = MAX_DEPTH
    for enemy in enemies:
        if enemy["health"] <= 0:
            continue
        dx = enemy["x"] - player_x
        dy = enemy["y"] - player_y
        distance = math.hypot(dx, dy)
        enemy_angle = math.atan2(dy, dx)
        delta_angle = enemy_angle - player_angle
        delta_angle = math.atan2(math.sin(delta_angle), math.cos(delta_angle))
        # If the enemy lies within a 5° cone in front.
        if abs(delta_angle) < math.radians(5):
            if distance < hit_distance:
                hit_distance = distance
                hit_enemy = enemy
    if hit_enemy:
        hit_enemy["health"] -= 1
        if hit_enemy["health"] <= 0:
            score += 100

def reload_gun():
    """Reload the gun (instant reload)."""
    global player_ammo
    player_ammo = max_ammo

def handle_input(dt):
    """Process WASD input: W/S to move, A/D to rotate."""
    global player_x, player_y, player_angle
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_x += math.cos(player_angle) * player_speed * dt
        player_y += math.sin(player_angle) * player_speed * dt
    if keys[pygame.K_s]:
        player_x -= math.cos(player_angle) * player_speed * dt
        player_y -= math.sin(player_angle) * player_speed * dt
    if keys[pygame.K_a]:
        player_angle -= turn_speed * dt
    if keys[pygame.K_d]:
        player_angle += turn_speed * dt

def draw_hud():
    """Draw the health bar, ammo count, and score."""
    # Health bar (top left)
    bar_width = 200
    bar_height = 20
    health_ratio = player_health / max_health
    pygame.draw.rect(screen, (255, 0, 0), (20, 20, bar_width, bar_height))
    pygame.draw.rect(screen, (0, 255, 0), (20, 20, int(bar_width * health_ratio), bar_height))
    draw_text(screen, f"Health: {int(player_health)}", 16, (255, 255, 255), (20 + bar_width//2, 20 + bar_height//2))
    # Ammo (top right)
    ammo_text = f"Ammo: {player_ammo}/{max_ammo}"
    draw_text(screen, ammo_text, 16, (255, 255, 255), (SCREEN_WIDTH - 100, 20 + bar_height//2))
    # Score (top center)
    draw_text(screen, f"Score: {score}", 16, (255, 255, 0), (SCREEN_WIDTH // 2, 20 + bar_height//2))

def draw_start_screen():
    """Display the start screen."""
    screen.fill((0, 0, 0))
    draw_text(screen, "Zombie FPS – Stickman Attack", 36, (255, 255, 255), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
    draw_text(screen, "Press any key to start", 24, (255, 255, 255), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
    pygame.display.flip()

def draw_game_over():
    """Display the game-over screen."""
    screen.fill((0, 0, 0))
    draw_text(screen, "Game Over", 48, (255, 0, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
    draw_text(screen, f"Score: {score}", 36, (255, 255, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    draw_text(screen, "Press R to Restart", 24, (255, 255, 255), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

# --- Main Game Loop ---
running = True
while running:
    dt = clock.tick(60) / 1000.0

    if game_state == "start":
        draw_start_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                game_state = "playing"

    elif game_state == "playing":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            # Right mouse button shoots
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    shoot()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reload_gun()

        handle_input(dt)
        update_enemies(dt)
        if player_health <= 0:
            game_state = "game_over"

        # --- Rendering the Scene ---
        screen.fill((100, 100, 100))
        draw_walls()
        # Sort enemies by distance so closer ones are drawn last (on top)
        sorted_enemies = sorted(enemies, key=lambda e: math.hypot(e["x"] - player_x, e["y"] - player_y), reverse=True)
        for enemy in sorted_enemies:
            if enemy["health"] > 0:
                draw_enemy(enemy)
        draw_hud()
        pygame.display.flip()

    elif game_state == "game_over":
        draw_game_over()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset game state
                    player_x = 100.0
                    player_y = 100.0
                    player_angle = 0.0
                    player_health = max_health
                    player_ammo = max_ammo
                    score = 0
                    spawn_enemies(5)
                    game_state = "playing"

pygame.quit()
sys.exit()
