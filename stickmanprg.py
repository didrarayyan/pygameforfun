import pygame, sys, random, math

# --- Initialize Pygame ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stickman RPG Fighter")
clock = pygame.time.Clock()

# --- Colors ---
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
GRAY    = (100, 100, 100)
BLUE    = (50, 100, 255)
RED     = (255, 50, 50)
GREEN   = (50, 255, 50)
YELLOW  = (255, 255, 0)
BROWN   = (139, 69, 19)
SKYBLUE = (135, 206, 235)
GRASS   = (34, 139, 34)

# --- Global Game State ---
# "start", "playing", "game_over"
game_state = "start"
score = 0

# --- Utility Functions ---
def draw_text(surface, text, size, color, center):
    font = pygame.font.SysFont("Arial", size)
    txt_surface = font.render(text, True, color)
    txt_rect = txt_surface.get_rect(center=center)
    surface.blit(txt_surface, txt_rect)

def draw_button(surface, text, rect, button_color, text_color):
    pygame.draw.rect(surface, button_color, rect)
    pygame.draw.rect(surface, WHITE, rect, 2)  # border
    font = pygame.font.SysFont("Arial", 24)
    txt_surface = font.render(text, True, text_color)
    txt_rect = txt_surface.get_rect(center=rect.center)
    surface.blit(txt_surface, txt_rect)

# --- Environment Drawing ---
def draw_environment():
    # Sky
    screen.fill(SKYBLUE)
    # Ground
    ground_rect = pygame.Rect(0, HEIGHT * 0.6, WIDTH, HEIGHT * 0.4)
    pygame.draw.rect(screen, GRASS, ground_rect)
    # Draw some stick trees for decoration
    for i in range(5):
        tree_x = random.randint(50, WIDTH - 50)
        tree_y = int(HEIGHT * 0.6) + random.randint(10, 40)
        # Trunk
        pygame.draw.line(screen, BROWN, (tree_x, tree_y), (tree_x, tree_y - 50), 6)
        # Branches / leaves (simple circle)
        pygame.draw.circle(screen, GREEN, (tree_x, tree_y - 60), 20)

# --- Stickman Drawing ---
def draw_stickman(x, y, facing_right, color, is_attacking=False):
    """
    Draws a stickman at (x,y) with head centered above body.
    'facing_right' determines the direction of the sword.
    If is_attacking is True, draw a sword slash.
    """
    head_radius = 12
    body_length = 40
    arm_length = 25
    leg_length = 30
    # Head (circle)
    head_center = (int(x), int(y - body_length - head_radius))
    pygame.draw.circle(screen, color, head_center, head_radius, 2)
    # Body (vertical line)
    body_top = (x, y - body_length)
    body_bottom = (x, y)
    pygame.draw.line(screen, color, body_top, body_bottom, 2)
    # Arms (diagonal lines)
    left_arm = (x - arm_length, y - body_length + 10)
    right_arm = (x + arm_length, y - body_length + 10)
    pygame.draw.line(screen, color, (x, y - body_length + 10), left_arm, 2)
    pygame.draw.line(screen, color, (x, y - body_length + 10), right_arm, 2)
    # Legs (diagonal lines)
    left_leg = (x - leg_length, y + leg_length)
    right_leg = (x + leg_length, y + leg_length)
    pygame.draw.line(screen, color, body_bottom, left_leg, 2)
    pygame.draw.line(screen, color, body_bottom, right_leg, 2)
    # Sword: drawn from the right arm if facing right, left arm otherwise.
    sword_offset = 15
    if facing_right:
        sword_start = (x + 5, y - body_length + 10)
        sword_end = (sword_start[0] + sword_offset, sword_start[1])
    else:
        sword_start = (x - 5, y - body_length + 10)
        sword_end = (sword_start[0] - sword_offset, sword_start[1])
    pygame.draw.line(screen, GRAY, sword_start, sword_end, 3)
    # If attacking, draw an extra arc or slash line
    if is_attacking:
        if facing_right:
            slash_start = (sword_end[0], sword_end[1] - 10)
            slash_end = (sword_end[0] + 15, sword_end[1] + 10)
        else:
            slash_start = (sword_end[0], sword_end[1] - 10)
            slash_end = (sword_end[0] - 15, sword_end[1] + 10)
        pygame.draw.line(screen, YELLOW, slash_start, slash_end, 3)

# --- Player Class ---
class Player:
    def __init__(self):
        self.x = WIDTH // 4
        self.y = int(HEIGHT * 0.75)
        self.health = 100
        self.max_health = 100
        self.speed = 200  # pixels per second
        self.attack_cooldown = 0.5  # seconds
        self.attack_timer = 0
        self.attacking = False
        self.facing_right = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        # Movement (arrow keys)
        if keys[pygame.K_LEFT]:
            self.x -= self.speed * dt
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.x += self.speed * dt
            self.facing_right = True
        if keys[pygame.K_UP]:
            self.y -= self.speed * dt
        if keys[pygame.K_DOWN]:
            self.y += self.speed * dt
        # Boundaries (arena limits)
        self.x = max(20, min(WIDTH - 20, self.x))
        self.y = max(int(HEIGHT*0.6)+20, min(HEIGHT - 20, self.y))
        # Update attack timer
        if self.attack_timer > 0:
            self.attack_timer -= dt
        else:
            self.attacking = False

    def attack(self):
        if self.attack_timer <= 0:
            self.attacking = True
            self.attack_timer = self.attack_cooldown
            return True
        return False

    def draw(self):
        draw_stickman(self.x, self.y, self.facing_right, BLUE, self.attacking)
        # Draw health bar above player
        bar_width = 60
        bar_height = 8
        health_ratio = self.health / self.max_health
        bar_x = self.x - bar_width // 2
        bar_y = self.y - 80
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

# --- Enemy Class ---
class Enemy:
    def __init__(self):
        # Spawn enemy at a random position in the arena (but not too close to the player spawn)
        self.x = random.randint(WIDTH//2, WIDTH - 50)
        self.y = random.randint(int(HEIGHT*0.6)+50, HEIGHT - 50)
        self.health = 60
        self.max_health = 60
        self.speed = 120
        self.attack_range = 60
        self.attack_cooldown = 1.0
        self.attack_timer = 0
        # Randomly decide facing direction based on position relative to player later.
        self.facing_right = False
        self.attacking = False

    def update(self, dt, player):
        # Move toward the player if not in attack range
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.hypot(dx, dy)
        if distance > self.attack_range:
            # Normalize direction
            if distance != 0:
                self.x += (dx / distance) * self.speed * dt
                self.y += (dy / distance) * self.speed * dt
            self.attacking = False
        else:
            # In range: attack periodically
            if self.attack_timer <= 0:
                self.attacking = True
                self.attack_timer = self.attack_cooldown
                # Inflict damage on player
                player.health -= 15
                if player.health < 0:
                    player.health = 0
            else:
                self.attacking = False
        # Update attack timer
        if self.attack_timer > 0:
            self.attack_timer -= dt
        # Update facing direction: face toward player
        self.facing_right = True if dx >= 0 else False

    def draw(self):
        draw_stickman(self.x, self.y, self.facing_right, RED, self.attacking)
        # Draw enemy health bar above enemy
        bar_width = 50
        bar_height = 6
        health_ratio = self.health / self.max_health
        bar_x = self.x - bar_width // 2
        bar_y = self.y - 70
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

# --- Initialize Player and Enemy ---
player = Player()
enemy = Enemy()

# --- Game State Management Functions ---
def reset_game():
    global player, enemy, score
    player = Player()
    enemy = Enemy()
    score = 0

# --- Start Screen ---
def draw_start_screen():
    screen.fill(BLACK)
    draw_text(screen, "Stickman RPG Fighter", 48, WHITE, (WIDTH//2, HEIGHT//3))
    # Start and Exit buttons
    start_rect = pygame.Rect(0, 0, 200, 50)
    start_rect.center = (WIDTH//2, HEIGHT//2)
    exit_rect = pygame.Rect(0, 0, 200, 50)
    exit_rect.center = (WIDTH//2, HEIGHT//2 + 70)
    draw_button(screen, "Start", start_rect, GRAY, WHITE)
    draw_button(screen, "Exit", exit_rect, GRAY, WHITE)
    return start_rect, exit_rect

# --- Game Over Screen ---
def draw_game_over_screen():
    screen.fill(BLACK)
    draw_text(screen, "Game Over", 48, RED, (WIDTH//2, HEIGHT//3))
    draw_text(screen, f"Score: {score}", 36, YELLOW, (WIDTH//2, HEIGHT//3 + 50))
    # Retry and Title buttons
    retry_rect = pygame.Rect(0, 0, 200, 50)
    retry_rect.center = (WIDTH//2, HEIGHT//2)
    title_rect = pygame.Rect(0, 0, 200, 50)
    title_rect.center = (WIDTH//2, HEIGHT//2 + 70)
    draw_button(screen, "Retry", retry_rect, GRAY, WHITE)
    draw_button(screen, "Title", title_rect, GRAY, WHITE)
    return retry_rect, title_rect

# --- Main Game Loop ---
running = True
while running:
    dt = clock.tick(60) / 1000.0  # Delta time in seconds

    if game_state == "start":
        start_button, exit_button = draw_start_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    reset_game()
                    game_state = "playing"
                elif exit_button.collidepoint(event.pos):
                    running = False
        pygame.display.flip()

    elif game_state == "playing":
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                # Attack when SPACE is pressed
                if event.key == pygame.K_SPACE:
                    if player.attack():
                        # Check if enemy is in attack range
                        dx = enemy.x - player.x
                        dy = enemy.y - player.y
                        if math.hypot(dx, dy) < 80:
                            enemy.health -= 20
                            if enemy.health <= 0:
                                score += 100
                                enemy = Enemy()  # spawn a new enemy

        # --- Update Game ---
        player.update(dt)
        enemy.update(dt, player)
        # Check if player is defeated
        if player.health <= 0:
            game_state = "game_over"

        # --- Draw the Scene ---
        draw_environment()
        # Draw arena boundaries (optional)
        pygame.draw.line(screen, BLACK, (0, int(HEIGHT*0.6)), (WIDTH, int(HEIGHT*0.6)), 3)
        # Draw player and enemy
        player.draw()
        enemy.draw()
        # Draw player's overall health bar (top left) and score
        health_bar_width = 200
        health_bar_height = 20
        pygame.draw.rect(screen, RED, (20, 20, health_bar_width, health_bar_height))
        health_ratio = player.health / player.max_health
        pygame.draw.rect(screen, GREEN, (20, 20, int(health_bar_width * health_ratio), health_bar_height))
        draw_text(screen, f"Score: {score}", 24, WHITE, (WIDTH - 100, 30))
        pygame.display.flip()

    elif game_state == "game_over":
        retry_button, title_button = draw_game_over_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_button.collidepoint(event.pos):
                    reset_game()
                    game_state = "playing"
                elif title_button.collidepoint(event.pos):
                    game_state = "start"
        pygame.display.flip()

pygame.quit()
sys.exit()
