import pygame, sys, random, math

# --- Initialize Pygame and Set Up Screen ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Old School Space Shooter")
clock = pygame.time.Clock()

# --- Colors ---
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
GRAY    = (100, 100, 100)
BLUE    = (50, 150, 255)
RED     = (255, 50, 50)
YELLOW  = (255, 215, 0)
DARKBLUE= (10, 10, 30)

# --- Game States ---
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

# --- Starfield for Background ---
class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(20, 80)
        self.size = random.randint(1, 3)
    
    def update(self, dt):
        self.y += self.speed * dt
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)
    
    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size)

stars = [Star() for _ in range(50)]

# --- Player Ship Class ---
class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT - 80
        self.speed = 250  # pixels per second
        self.size = 20    # for drawing the triangle
        self.bullet_cooldown = 0.3  # seconds between shots
        self.fire_timer = 0
    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= self.speed * dt
        if keys[pygame.K_RIGHT]:
            self.x += self.speed * dt
        if keys[pygame.K_UP]:
            self.y -= self.speed * dt
        if keys[pygame.K_DOWN]:
            self.y += self.speed * dt
        
        # Keep within screen bounds
        self.x = max(self.size, min(SCREEN_WIDTH - self.size, self.x))
        self.y = max(self.size, min(SCREEN_HEIGHT - self.size, self.y))
        
        # Update auto-fire timer
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = self.bullet_cooldown
            bullets.append(Bullet(self.x, self.y - self.size))
    
    def draw(self, surface):
        # Draw a triangle pointing upward
        point1 = (int(self.x), int(self.y - self.size))
        point2 = (int(self.x - self.size), int(self.y + self.size))
        point3 = (int(self.x + self.size), int(self.y + self.size))
        pygame.draw.polygon(surface, BLUE, [point1, point2, point3])

# --- Bullet Class ---
class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 4
        self.speed = 400  # pixels per second
    
    def update(self, dt):
        self.y -= self.speed * dt
    
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)
    
    def off_screen(self):
        return self.y < 0

# --- Enemy Ship Class ---
class Enemy:
    def __init__(self):
        self.x = random.randint(40, SCREEN_WIDTH - 40)
        self.y = -40
        self.speed = random.randint(80, 150)
        self.size = 20
        self.health = 1
    
    def update(self, dt):
        self.y += self.speed * dt
    
    def draw(self, surface):
        # Draw a red triangle pointing downward
        point1 = (int(self.x), int(self.y + self.size))
        point2 = (int(self.x - self.size), int(self.y - self.size))
        point3 = (int(self.x + self.size), int(self.y - self.size))
        pygame.draw.polygon(surface, RED, [point1, point2, point3])
    
    def off_screen(self):
        return self.y - self.size > SCREEN_HEIGHT

# --- Coin Class ---
class Coin:
    def __init__(self):
        self.x = random.randint(30, SCREEN_WIDTH - 30)
        self.y = -30
        self.radius = 10
        self.speed = 100
    def update(self, dt):
        self.y += self.speed * dt
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)
    def off_screen(self):
        return self.y - self.radius > SCREEN_HEIGHT

# --- Initialize Game Objects ---
player = Player()
bullets = []
enemies = []
coins = []
enemy_spawn_timer = 0
coin_spawn_timer = 0

# --- Title Screen Function ---
def draw_title_screen():
    screen.fill(DARKBLUE)
    draw_text(screen, "Space Shooter", 60, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    start_rect = pygame.Rect(0, 0, 200, 50)
    start_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    exit_rect = pygame.Rect(0, 0, 200, 50)
    exit_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Start", start_rect, GRAY, WHITE)
    draw_button(screen, "Exit", exit_rect, GRAY, WHITE)
    return start_rect, exit_rect

# --- Game Over Screen Function ---
def draw_game_over_screen():
    screen.fill(DARKBLUE)
    draw_text(screen, "Game Over", 60, RED, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    draw_text(screen, f"Score: {score}", 40, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
    retry_rect = pygame.Rect(0, 0, 200, 50)
    retry_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    title_rect = pygame.Rect(0, 0, 200, 50)
    title_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Retry", retry_rect, GRAY, WHITE)
    draw_button(screen, "Title", title_rect, GRAY, WHITE)
    return retry_rect, title_rect

# --- Reset Game Function ---
def reset_game():
    global player, bullets, enemies, coins, enemy_spawn_timer, coin_spawn_timer, score
    player = Player()
    bullets = []
    enemies = []
    coins = []
    enemy_spawn_timer = 0
    coin_spawn_timer = 0
    score = 0

# --- Main Game Loop ---
running = True
while running:
    dt = clock.tick(60) / 1000.0  # delta time in seconds
    
    if game_state == "start":
        start_button, exit_button = draw_title_screen()
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # --- Update Background Stars ---
        for star in stars:
            star.update(dt)
        
        # --- Update Player ---
        player.update(dt)
        
        # --- Auto-fire Bullets are added in player's update ---
        for bullet in bullets:
            bullet.update(dt)
        bullets = [b for b in bullets if not b.off_screen()]
        
        # --- Spawn Enemies ---
        enemy_spawn_timer -= dt
        if enemy_spawn_timer <= 0:
            enemy_spawn_timer = random.uniform(0.8, 1.5)
            enemies.append(Enemy())
        for enemy in enemies:
            enemy.update(dt)
        enemies = [e for e in enemies if not e.off_screen()]
        
        # --- Spawn Coins ---
        coin_spawn_timer -= dt
        if coin_spawn_timer <= 0:
            coin_spawn_timer = random.uniform(1.5, 3.0)
            coins.append(Coin())
        for coin in coins:
            coin.update(dt)
        coins = [c for c in coins if not c.off_screen()]
        
        # --- Check Collisions ---
        # Bullets with Enemies
        for bullet in bullets[:]:
            for enemy in enemies[:]:
                dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                if dist < enemy.size:
                    bullets.remove(bullet)
                    enemies.remove(enemy)
                    score += 50
                    break
        # Player with Enemies
        for enemy in enemies:
            dist = math.hypot(player.x - enemy.x, player.y - enemy.y)
            if dist < player.size + enemy.size:
                game_state = "game_over"
        # Player with Coins
        for coin in coins[:]:
            dist = math.hypot(player.x - coin.x, player.y - coin.y)
            if dist < player.size + coin.radius:
                coins.remove(coin)
                score += 20
        
        # --- Drawing ---
        screen.fill(BLACK)
        # Draw starfield
        for star in stars:
            star.draw(screen)
        # Draw coins
        for coin in coins:
            coin.draw(screen)
        # Draw enemies
        for enemy in enemies:
            enemy.draw(screen)
        # Draw bullets
        for bullet in bullets:
            bullet.draw(screen)
        # Draw player
        player.draw(screen)
        # Draw HUD (score)
        draw_text(screen, f"Score: {score}", 24, WHITE, (70, 20))
        
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
