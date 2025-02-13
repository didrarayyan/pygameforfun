import pygame, sys, random, math

# --- Initialization ---
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Dodge Ball Challenge")
clock = pygame.time.Clock()

# --- Colors ---
WHITE    = (255, 255, 255)
BLACK    = (0, 0, 0)
GRAY     = (100, 100, 100)
DARKGRAY = (50, 50, 50)
RED      = (220, 20, 60)
GREEN    = (50, 205, 50)
BLUE     = (50, 150, 255)
YELLOW   = (255, 215, 0)
ORANGE   = (255, 140, 0)
PURPLE   = (148, 0, 211)

# --- Global Variables & Game States ---
game_state = "title"      # can be "title", "difficulty", "playing", "game_over"
score = 0                 # survival time in seconds
difficulty = None         # will be set to a dict with game parameters

# Global parameters (set during difficulty selection)
ball_spawn_interval = 2.0  # seconds between ball spawns (Easy default)
ball_speed_multiplier = 1.0

# --- Utility Functions ---
def draw_text(surf, text, size, color, center):
    font = pygame.font.SysFont("arial", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    surf.blit(text_surface, text_rect)

def draw_button(surf, text, rect, button_color, text_color):
    pygame.draw.rect(surf, button_color, rect)
    pygame.draw.rect(surf, WHITE, rect, 2)
    draw_text(surf, text, 24, text_color, rect.center)

# --- Classes ---
class Player:
    def __init__(self):
        self.radius = 15
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.speed = 300  # pixels per second

    def update(self, dt):
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed * dt
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed * dt

        self.x += dx
        self.y += dy

        # Keep player within screen bounds
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

    def draw(self, surf):
        pygame.draw.circle(surf, BLUE, (int(self.x), int(self.y)), self.radius)
        # Draw a small shield outline for style
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.radius, 2)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

class Ball:
    def __init__(self):
        self.radius = random.randint(10, 20)
        # Spawn from a random edge:
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            self.x = random.uniform(self.radius, SCREEN_WIDTH - self.radius)
            self.y = -self.radius
        elif edge == "bottom":
            self.x = random.uniform(self.radius, SCREEN_WIDTH - self.radius)
            self.y = SCREEN_HEIGHT + self.radius
        elif edge == "left":
            self.x = -self.radius
            self.y = random.uniform(self.radius, SCREEN_HEIGHT - self.radius)
        else:  # right
            self.x = SCREEN_WIDTH + self.radius
            self.y = random.uniform(self.radius, SCREEN_HEIGHT - self.radius)

        # Set a random direction toward the screen center plus some randomness
        dir_vector = pygame.math.Vector2(SCREEN_WIDTH/2 - self.x, SCREEN_HEIGHT/2 - self.y)
        if dir_vector.length() == 0:
            dir_vector = pygame.math.Vector2(1, 0)
        else:
            dir_vector = dir_vector.normalize()
        angle_offset = random.uniform(-math.pi/4, math.pi/4)
        cos_a = math.cos(angle_offset)
        sin_a = math.sin(angle_offset)
        rotated = pygame.math.Vector2(dir_vector.x * cos_a - dir_vector.y * sin_a,
                                        dir_vector.x * sin_a + dir_vector.y * cos_a)
        self.vx = rotated.x * random.uniform(100, 200) * ball_speed_multiplier
        self.vy = rotated.y * random.uniform(100, 200) * ball_speed_multiplier

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bounce off walls:
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx *= -1
        if self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx *= -1
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy *= -1
        if self.y + self.radius > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            self.vy *= -1

    def draw(self, surf):
        pygame.draw.circle(surf, ORANGE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.radius, 2)

    def collides_with(self, player):
        dx = self.x - player.x
        dy = self.y - player.y
        distance = math.hypot(dx, dy)
        return distance < self.radius + player.radius

# --- Global Game Objects (Initialized on game start) ---
player = None
balls = []
ball_spawn_timer = 0

# --- Difficulty Settings ---
difficulties = {
    "Easy":    {"spawn_interval": 2.0, "speed_multiplier": 1.0},
    "Medium":  {"spawn_interval": 1.5, "speed_multiplier": 1.5},
    "Hard":    {"spawn_interval": 1.0, "speed_multiplier": 2.0}
}

# --- Reset / Initialize Game ---
def init_game():
    global player, balls, ball_spawn_timer, score, ball_spawn_interval, ball_speed_multiplier
    player = Player()
    balls = []
    ball_spawn_timer = 0
    score = 0
    # ball_spawn_interval and ball_speed_multiplier are set during difficulty selection

# --- Menus ---
def title_screen():
    screen.fill(DARKGRAY)
    draw_text(screen, "Dodge Ball Challenge", 60, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    play_rect = pygame.Rect(0, 0, 250, 50)
    play_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    exit_rect = pygame.Rect(0, 0, 250, 50)
    exit_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Play", play_rect, GRAY, WHITE)
    draw_button(screen, "Exit", exit_rect, GRAY, WHITE)
    return play_rect, exit_rect

def difficulty_screen():
    screen.fill(DARKGRAY)
    draw_text(screen, "Select Difficulty", 60, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    btn_width = 200
    btn_height = 50
    spacing = 20
    total_height = 3 * btn_height + 2 * spacing
    start_y = SCREEN_HEIGHT//2 - total_height//2
    easy_rect = pygame.Rect(0, 0, btn_width, btn_height)
    medium_rect = pygame.Rect(0, 0, btn_width, btn_height)
    hard_rect = pygame.Rect(0, 0, btn_width, btn_height)
    easy_rect.center = (SCREEN_WIDTH//2, start_y + btn_height//2)
    medium_rect.center = (SCREEN_WIDTH//2, start_y + btn_height + spacing + btn_height//2)
    hard_rect.center = (SCREEN_WIDTH//2, start_y + 2*(btn_height + spacing) + btn_height//2)
    draw_button(screen, "Easy", easy_rect, GRAY, WHITE)
    draw_button(screen, "Medium", medium_rect, GRAY, WHITE)
    draw_button(screen, "Hard", hard_rect, GRAY, WHITE)
    return easy_rect, medium_rect, hard_rect

def game_over_screen():
    screen.fill(BLACK)
    draw_text(screen, "Game Over", 60, RED, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    draw_text(screen, f"Survived: {int(score)} sec", 40, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 60))
    retry_rect = pygame.Rect(0, 0, 250, 50)
    title_rect = pygame.Rect(0, 0, 250, 50)
    retry_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    title_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Retry", retry_rect, GRAY, WHITE)
    draw_button(screen, "Title", title_rect, GRAY, WHITE)
    return retry_rect, title_rect

# --- Main Game Loop ---
running = True
state = "title"  # possible states: title, difficulty, playing, game_over

init_game()

while running:
    dt = clock.tick(60) / 1000.0  # delta time in seconds

    if state == "title":
        play_button, exit_button = title_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    state = "difficulty"
                elif exit_button.collidepoint(event.pos):
                    running = False
        pygame.display.flip()

    elif state == "difficulty":
        easy_btn, medium_btn, hard_btn = difficulty_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_btn.collidepoint(event.pos):
                    difficulty = "Easy"
                elif medium_btn.collidepoint(event.pos):
                    difficulty = "Medium"
                elif hard_btn.collidepoint(event.pos):
                    difficulty = "Hard"
                if difficulty:
                    ball_spawn_interval = difficulties[difficulty]["spawn_interval"]
                    ball_speed_multiplier = difficulties[difficulty]["speed_multiplier"]
                    init_game()
                    state = "playing"
        pygame.display.flip()

    elif state == "playing":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Update game objects
        player.update(dt)
        for ball in balls:
            ball.update(dt)

        # Spawn new balls based on timer
        ball_spawn_timer -= dt
        if ball_spawn_timer <= 0:
            ball_spawn_timer = ball_spawn_interval
            balls.append(Ball())

        # Increase score based on time survived
        score += dt

        # Check for collisions
        for ball in balls:
            if ball.collides_with(player):
                state = "game_over"
                break

        # Draw the game
        screen.fill(DARKGRAY)
        player.draw(screen)
        for ball in balls:
            ball.draw(screen)
        draw_text(screen, f"Time: {int(score)} sec", 24, WHITE, (70, 20))
        pygame.display.flip()

    elif state == "game_over":
        retry_btn, title_btn = game_over_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_btn.collidepoint(event.pos):
                    init_game()
                    state = "playing"
                elif title_btn.collidepoint(event.pos):
                    state = "title"
        pygame.display.flip()

pygame.quit()
sys.exit()
