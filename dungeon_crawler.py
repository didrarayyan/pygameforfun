import pygame, sys, random, math

# === Initialization ===
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dungeon Crawler Adventure")
clock = pygame.time.Clock()

# === Global Constants & Colors ===
TILE_SIZE = 40
FONT_NAME = pygame.font.match_font("arial")

WHITE     = (255, 255, 255)
BLACK     = (0, 0, 0)
GRAY      = (100, 100, 100)
DARKGRAY  = (40, 40, 40)
LIGHTGRAY = (160, 160, 160)
RED       = (220, 20, 60)
GREEN     = (50, 205, 50)
GOLD      = (255, 215, 0)
BROWN     = (139, 69, 19)
SKYBLUE   = (135, 206, 235)
BLUE      = (50, 150, 255)
DUNGEON_FLOOR = (200, 200, 180)

# === Game States ===
# "title", "playing", "level_complete", "game_over", "win"
game_state = "title"
score = 0
current_level = 0  # 0-based: levels 0-4 (Level 5 is boss)

# === Level Maps ===
# Legend:
#   W = Wall
#   . = Floor (unused, simply background)
#   C = Coin
#   E = Enemy spawn (regular enemy)
#   B = Boss spawn (only in Level 5)
#   P = Player spawn
#   D = Exit door

level1 = [
    "WWWWWWWWWWWWWWWWWW",
    "W......C.........W",
    "W..WWW.....WWW...W",
    "W..W...E...W..C..W",
    "W..W........W....W",
    "W..W..WWW...W....W",
    "W....W.PW.......DW",
    "W..C.W...W...WWW.W",
    "W......C.W.......W",
    "WWWWWWWWWWWWWWWWWW"
]

level2 = [
    "WWWWWWWWWWWWWWWWWW",
    "W...C......E.....W",
    "W..WWW....WWW....W",
    "W..W...E..W..C...W",
    "W..W..........E..W",
    "W..W..WWW...W....W",
    "W....W.PW....E..DW",
    "W..C.W...W...WWW.W",
    "W...E..C.W.......W",
    "WWWWWWWWWWWWWWWWWW"
]

level3 = [
    "WWWWWWWWWWWWWWWWWW",
    "W.C....E...C.....W",
    "W..WWW..WWW.WWWW.W",
    "W..W...E.W..W.C..W",
    "W..W...WWW..W....W",
    "W..W..WWW...W.E..W",
    "W....W.PW...E...DW",
    "W..C.W...W...WWW.W",
    "W...E..C.W..E....W",
    "WWWWWWWWWWWWWWWWWW"
]

level4 = [
    "WWWWWWWWWWWWWWWWWW",
    "W.C.E..E...C.E...W",
    "W..WWW..WWW.WWWW.W",
    "W.EW...E.W..W.CE.W",
    "W..W...WWW..W....W",
    "W..W..WWW...W.E..W",
    "W....W.PW...E...DW",
    "W.C.W...W.E.WWW.EW",
    "W...E..C.W..E....W",
    "WWWWWWWWWWWWWWWWWW"
]

level5 = [
    "WWWWWWWWWWWWWWWWWW",
    "W.C..............W",
    "W..WWW.....WWW...W",
    "W..W...B...W..C..W",
    "W..W........W....W",
    "W..W..WWW...W....W",
    "W....W.PW.......DW",
    "W..C.W...W...WWW.W",
    "W........W.......W",
    "WWWWWWWWWWWWWWWWWW"
]

levels = [level1, level2, level3, level4, level5]

# === Utility Functions ===
def draw_text(surf, text, size, color, center):
    font = pygame.font.Font(FONT_NAME, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    surf.blit(text_surface, text_rect)

def draw_button(surf, text, rect, button_color, text_color):
    pygame.draw.rect(surf, button_color, rect)
    pygame.draw.rect(surf, WHITE, rect, 2)
    draw_text(surf, text, 24, text_color, rect.center)

# === Level Parser ===
def parse_level(map_data):
    walls = []
    coins = []
    enemies = []
    player_start = None
    exit_rect = None
    rows = len(map_data)
    cols = len(map_data[0])
    for row in range(rows):
        for col in range(cols):
            x = col * TILE_SIZE
            y = row * TILE_SIZE
            tile = map_data[row][col]
            if tile == "W":
                walls.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
            elif tile == "C":
                coins.append(Coin(x + TILE_SIZE//2, y + TILE_SIZE//2))
            elif tile == "E":
                enemies.append(Enemy(x + TILE_SIZE//2 - 15, y + TILE_SIZE//2 - 15))
            elif tile == "B":
                enemies.append(BossEnemy(x + TILE_SIZE//2 - 30, y + TILE_SIZE//2 - 30))
            elif tile == "P":
                player_start = (x + TILE_SIZE//2 - 15, y + TILE_SIZE//2 - 15)
            elif tile == "D":
                exit_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    return walls, coins, enemies, player_start, exit_rect

# === Game Object Classes ===

class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.width = 30
        self.height = 30
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.health = 100
        self.max_health = 100
        self.speed = 200  # pixels per second
        self.attack_cooldown = 0.5
        self.attack_timer = 0
        self.attacking = False
        self.facing = pygame.math.Vector2(0, -1)  # default facing up

    def handle_input(self, dt, walls):
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

        if dx != 0 or dy != 0:
            self.facing = pygame.math.Vector2(dx, dy).normalize()

        # Horizontal movement and collision
        self.x += dx
        self.rect.x = int(self.x)
        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0:
                    self.rect.right = wall.left
                if dx < 0:
                    self.rect.left = wall.right
                self.x = self.rect.x

        # Vertical movement and collision
        self.y += dy
        self.rect.y = int(self.y)
        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0:
                    self.rect.bottom = wall.top
                if dy < 0:
                    self.rect.top = wall.bottom
                self.y = self.rect.y

    def update(self, dt, walls):
        self.handle_input(dt, walls)
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

    def draw(self, surf):
        pygame.draw.circle(surf, BLUE, self.rect.center, self.width//2)
        if self.attacking:
            end_pos = (self.rect.centerx + int(self.facing.x * 40),
                       self.rect.centery + int(self.facing.y * 40))
            pygame.draw.line(surf, GOLD, self.rect.center, end_pos, 4)
        bar_width = 40
        bar_height = 6
        health_ratio = self.health / self.max_health
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 10
        pygame.draw.rect(surf, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surf, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

class Enemy:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.width = 30
        self.height = 30
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.health = 50
        self.speed = 80
    def update(self, dt, player):
        direction = pygame.math.Vector2(player.rect.centerx - self.rect.centerx,
                                        player.rect.centery - self.rect.centery)
        if direction.length() != 0:
            direction = direction.normalize()
            self.x += direction.x * self.speed * dt
            self.y += direction.y * self.speed * dt
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)
    def draw(self, surf):
        pygame.draw.rect(surf, RED, self.rect)
        bar_width = 30
        bar_height = 4
        health_ratio = self.health / 50
        bar_x = self.rect.x
        bar_y = self.rect.y - 8
        pygame.draw.rect(surf, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surf, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

class BossEnemy:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.width = 60
        self.height = 60
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.health = 300
        self.speed = 50
    def update(self, dt, player):
        direction = pygame.math.Vector2(player.rect.centerx - self.rect.centerx,
                                        player.rect.centery - self.rect.centery)
        if direction.length() != 0:
            direction = direction.normalize()
            self.x += direction.x * self.speed * dt
            self.y += direction.y * self.speed * dt
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)
    def draw(self, surf):
        pygame.draw.rect(surf, (139,0,0), self.rect)
        bar_width = self.width
        bar_height = 6
        health_ratio = self.health / 300
        bar_x = self.rect.x
        bar_y = self.rect.y - 10
        pygame.draw.rect(surf, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surf, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius,
                                self.radius*2, self.radius*2)
    def draw(self, surf):
        pygame.draw.circle(surf, GOLD, (int(self.x), int(self.y)), self.radius)

# === Global Game Variables (set in reset_game) ===
player = None
walls = []
coins = []
enemies = []
exit_rect = None

def reset_game():
    global player, walls, coins, enemies, exit_rect, score
    score = 0
    current_map = levels[current_level]
    walls, coins, enemies, player_start, exit_rect = parse_level(current_map)
    if player_start is None:
        player_start = (TILE_SIZE, TILE_SIZE)
    player = Player(*player_start)

# === Menu Screens ===
def draw_title_screen():
    screen.fill(DARKGRAY)
    draw_text(screen, "Dungeon Crawler Adventure", 60, GOLD, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    start_rect = pygame.Rect(0, 0, 250, 50)
    start_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    exit_rect_menu = pygame.Rect(0, 0, 250, 50)
    exit_rect_menu.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Start Game", start_rect, GRAY, WHITE)
    draw_button(screen, "Exit", exit_rect_menu, GRAY, WHITE)
    return start_rect, exit_rect_menu

def draw_level_complete_screen():
    screen.fill(BLACK)
    draw_text(screen, f"Level {current_level+1} Complete!", 60, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    draw_text(screen, f"Score: {score}", 40, GOLD, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
    next_rect = pygame.Rect(0, 0, 250, 50)
    next_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    title_rect = pygame.Rect(0, 0, 250, 50)
    title_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Next Level", next_rect, GRAY, WHITE)
    draw_button(screen, "Title", title_rect, GRAY, WHITE)
    return next_rect, title_rect

def draw_game_over_screen():
    screen.fill(BLACK)
    draw_text(screen, "Game Over", 60, RED, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    draw_text(screen, f"Score: {score}", 40, GOLD, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
    retry_rect = pygame.Rect(0, 0, 250, 50)
    retry_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    title_rect = pygame.Rect(0, 0, 250, 50)
    title_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Retry", retry_rect, GRAY, WHITE)
    draw_button(screen, "Title", title_rect, GRAY, WHITE)
    return retry_rect, title_rect

def draw_win_screen():
    screen.fill(BLACK)
    draw_text(screen, "Congratulations!", 60, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    draw_text(screen, "You defeated the boss and completed your adventure!", 40, GOLD, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
    draw_text(screen, f"Final Score: {score}", 36, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 100))
    title_rect = pygame.Rect(0, 0, 250, 50)
    title_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Title", title_rect, GRAY, WHITE)
    return title_rect

# === Draw the Dungeon Environment ===
def draw_level(surf):
    surf.fill(DUNGEON_FLOOR)
    rows = len(levels[current_level])
    cols = len(levels[current_level][0])
    for row in range(rows):
        for col in range(cols):
            x = col * TILE_SIZE
            y = row * TILE_SIZE
            tile = levels[current_level][row][col]
            if tile == "W":
                pygame.draw.rect(surf, LIGHTGRAY, (x, y, TILE_SIZE, TILE_SIZE))
            elif tile == "D":
                pygame.draw.rect(surf, BROWN, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(surf, BLACK, (x+5, y+5, TILE_SIZE-10, TILE_SIZE-10), 2)

# === Main Game Loop ===
running = True
reset_game()

while running:
    dt = clock.tick(60) / 1000.0

    if game_state == "title":
        start_button, exit_button = draw_title_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    current_level = 0
                    reset_game()
                    game_state = "playing"
                elif exit_button.collidepoint(event.pos):
                    running = False
        pygame.display.flip()

    elif game_state == "playing":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if player.attack():
                        attack_range = 50
                        attack_area = pygame.Rect(0, 0, attack_range, attack_range)
                        attack_area.center = (player.rect.centerx + int(player.facing.x * 30),
                                              player.rect.centery + int(player.facing.y * 30))
                        for enemy in enemies[:]:
                            if attack_area.colliderect(enemy.rect):
                                enemy.health -= 30
                                if enemy.health <= 0:
                                    enemies.remove(enemy)
                                    score += 100

        player.update(dt, walls)
        for enemy in enemies:
            enemy.update(dt, player)
        for coin in coins[:]:
            if player.rect.colliderect(coin.rect):
                coins.remove(coin)
                score += 20
        for enemy in enemies:
            if player.rect.colliderect(enemy.rect):
                player.health -= 30 * dt
                if player.health <= 0:
                    player.health = 0
                    game_state = "game_over"

        # Check for exit door collision to finish level
        if exit_rect and player.rect.colliderect(exit_rect):
            # For levels 1-4, finish immediately.
            # For Level 5 (boss level), require boss defeated (i.e. enemies list empty).
            if current_level < len(levels) - 1:
                game_state = "level_complete"
            elif current_level == len(levels) - 1:
                if len(enemies) == 0:
                    game_state = "win"

        draw_level(screen)
        for wall in walls:
            pygame.draw.rect(screen, DARKGRAY, wall, 2)
        for coin in coins:
            coin.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        player.draw(screen)
        draw_text(screen, f"Score: {score}", 24, BLACK, (60, 20))
        pygame.display.flip()

    elif game_state == "level_complete":
        next_button, title_button = draw_level_complete_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if next_button.collidepoint(event.pos):
                    current_level += 1
                    reset_game()
                    game_state = "playing"
                elif title_button.collidepoint(event.pos):
                    current_level = 0
                    game_state = "title"
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
                    current_level = 0
                    game_state = "title"
        pygame.display.flip()

    elif game_state == "win":
        title_button = draw_win_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if title_button.collidepoint(event.pos):
                    current_level = 0
                    game_state = "title"
        pygame.display.flip()

pygame.quit()
sys.exit()
