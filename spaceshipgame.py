import pygame, sys, random, math, io, wave
import numpy as np

# ---------------------------
# Initialization & Screen Setup
# ---------------------------
pygame.init()
pygame.mixer.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
# Fullscreen mode:
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Old School Space Shooter")
clock = pygame.time.Clock()

# ---------------------------
# Colors
# ---------------------------
BLACK    = (0, 0, 0)
WHITE    = (255, 255, 255)
GRAY     = (100, 100, 100)
DARKBLUE = (10, 10, 30)
BLUE     = (50, 150, 255)
RED      = (255, 50, 50)
YELLOW   = (255, 215, 0)
GREEN    = (50, 205, 50)
PURPLE   = (148, 0, 211)

# ---------------------------
# Game States & Global Variables
# ---------------------------
# Game states: "start", "instructions", "playing", "rest", "boss_victory", "game_over"
game_state = "start"
score = 0
boss = None          # Holds BossEnemy when boss battle begins
enemy_bullets = []   # Bullets fired by enemy ships
asteroids = []       # Asteroids (obstacles)
coins = []           # Coins (+50 points)
healthpacks = []     # Health packs (heal the player)
warning_shown = False

# Timers for new states:
instructions_timer = 5.0  # 5 seconds for instructions
rest_timer = 5.0          # 5 seconds of resting before boss battle

# ---------------------------
# Utility Functions
# ---------------------------
def draw_text(surface, text, size, color, center):
    font = pygame.font.SysFont("Arial", size)
    txt_surface = font.render(text, True, color)
    txt_rect = txt_surface.get_rect(center=center)
    surface.blit(txt_surface, txt_rect)

def draw_button(surface, text, rect, button_color, text_color):
    pygame.draw.rect(surface, button_color, rect)
    pygame.draw.rect(surface, WHITE, rect, 2)
    draw_text(surface, text, 24, text_color, rect.center)

# ---------------------------
# Sound Generation Functions
# ---------------------------
def generate_sound(frequency, duration, volume=1.0, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    wave_data = np.sin(2 * np.pi * frequency * t)
    wave_data = (wave_data * 32767 * volume).astype(np.int16)
    stereo_wave = np.column_stack((wave_data, wave_data))
    sound = pygame.sndarray.make_sound(stereo_wave)
    return sound

# "Pew" sound for player's firing
pew_sound = generate_sound(frequency=1000, duration=0.1, volume=0.7)
# Explosion sound
explosion_sound = generate_sound(frequency=100, duration=0.3, volume=0.8)

# ---------------------------
# Background Music (Title Screen)
# ---------------------------
def create_retro_music(duration=5, frequency=330, volume=0.3, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    data = np.sin(2 * np.pi * frequency * t) * volume
    data_int16 = (data * 32767).astype(np.int16)
    stereo = np.column_stack((data_int16, data_int16))
    bytes_io = io.BytesIO()
    with wave.open(bytes_io, 'wb') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(stereo.tobytes())
    bytes_io.seek(0)
    return bytes_io

music_file = create_retro_music(duration=5, frequency=330, volume=0.3)
pygame.mixer.music.load(music_file)
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# ---------------------------
# Explosion Animation Class
# ---------------------------
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0.5  # lasts 0.5 sec
        self.max_radius = 40
    def update(self, dt):
        self.timer -= dt
    def draw(self, surface):
        if self.timer > 0:
            radius = int(self.max_radius * (1 - self.timer / 0.5))
            alpha = int(255 * (self.timer / 0.5))
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 165, 0, alpha), (radius, radius), radius)
            surface.blit(s, (self.x - radius, self.y - radius))

# ---------------------------
# Starfield for Background
# ---------------------------
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

# ---------------------------
# Player Ship Class
# ---------------------------
class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT - 80
        self.speed = 250
        self.size = 20
        self.bullet_cooldown = 0.3
        self.fire_timer = 0
        self.health = 100
        self.max_health = 100
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
        self.x = max(self.size, min(SCREEN_WIDTH - self.size, self.x))
        self.y = max(self.size, min(SCREEN_HEIGHT - self.size, self.y))
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = self.bullet_cooldown
            bullets.append(Bullet(self.x, self.y - self.size))
            pew_sound.play()
    def draw(self, surface):
        point1 = (int(self.x), int(self.y - self.size))
        point2 = (int(self.x - self.size), int(self.y + self.size))
        point3 = (int(self.x + self.size), int(self.y + self.size))
        pygame.draw.polygon(surface, BLUE, [point1, point2, point3])
        bar_width = 50
        bar_height = 5
        health_ratio = self.health / self.max_health
        bar_x = self.x - bar_width/2
        bar_y = self.y - self.size - 10
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_ratio, bar_height))

# ---------------------------
# Bullet Class (Player)
# ---------------------------
class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 4
        self.speed = 400
    def update(self, dt):
        self.y -= self.speed * dt
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)
    def off_screen(self):
        return self.y < 0

# ---------------------------
# Enemy Bullet Class (Fired by Enemies)
# ---------------------------
class EnemyBullet:
    def __init__(self, x, y, target):
        self.x = x
        self.y = y
        self.radius = 4
        self.speed = 400
        dx = target.x - x
        dy = target.y - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        self.vx = dx / dist * self.speed
        self.vy = dy / dist * self.speed
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
    def draw(self, surface):
        pygame.draw.circle(surface, PURPLE, (int(self.x), int(self.y)), self.radius)
    def off_screen(self):
        return self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT

# ---------------------------
# Enemy Ship Class (Triangle that hovers and shoots)
# ---------------------------
class Enemy:
    def __init__(self):
        self.x = random.randint(40, SCREEN_WIDTH - 40)
        self.y = -40
        self.speed = random.randint(50, 100)
        self.size = 20
        self.health = 3
        self.max_health = 3
        self.fire_cooldown = random.uniform(1.5, 2.5)
        self.fire_timer = self.fire_cooldown
    def update(self, dt, player):
        speed_increase = score * 0.1
        self.y += (self.speed + speed_increase) * dt
        # Hover horizontally toward player's x position
        target_x = player.x
        dx = target_x - self.x
        horizontal_speed = 100 + score * 0.05
        if abs(dx) > 1:
            self.x += math.copysign(min(abs(dx), horizontal_speed * dt), dx)
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = self.fire_cooldown
            enemy_bullets.append(EnemyBullet(self.x, self.y, player))
    def draw(self, surface):
        point1 = (int(self.x), int(self.y + self.size))
        point2 = (int(self.x - self.size), int(self.y - self.size))
        point3 = (int(self.x + self.size), int(self.y - self.size))
        pygame.draw.polygon(surface, RED, [point1, point2, point3])
        bar_width = 40
        bar_height = 4
        health_ratio = self.health / self.max_health
        bar_x = self.x - bar_width/2
        bar_y = self.y - self.size - 10
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_ratio, bar_height))
    def off_screen(self):
        return self.y - self.size > SCREEN_HEIGHT

# ---------------------------
# Boss Enemy Class (Spawns at 4000 score)
# ---------------------------
class BossEnemy:
    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = -80
        self.speed = 50
        self.size = 40
        self.health = 30
        self.max_health = 30
        self.fire_cooldown = 0.8
        self.fire_timer = self.fire_cooldown
    def update(self, dt, player):
        self.y += self.speed * dt
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = self.fire_cooldown
            enemy_bullets.append(EnemyBullet(self.x, self.y, player))
    def draw(self, surface):
        point1 = (int(self.x), int(self.y + self.size))
        point2 = (int(self.x - self.size), int(self.y - self.size))
        point3 = (int(self.x + self.size), int(self.y - self.size))
        pygame.draw.polygon(surface, RED, [point1, point2, point3])
        bar_width = 80
        bar_height = 6
        health_ratio = self.health / self.max_health
        bar_x = self.x - bar_width/2
        bar_y = self.y - self.size - 15
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_ratio, bar_height))
    def off_screen(self):
        return self.y - self.size > SCREEN_HEIGHT

# ---------------------------
# Asteroid Class (Square obstacles, destructible)
# ---------------------------
class Asteroid:
    def __init__(self):
        self.x = random.randint(30, SCREEN_WIDTH - 30)
        self.y = -30
        self.size = random.randint(20, 40)
        self.speed = random.randint(80, 150)
    def update(self, dt):
        self.y += self.speed * dt
    def draw(self, surface):
        rect = pygame.Rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size)
        pygame.draw.rect(surface, GRAY, rect)
    def off_screen(self):
        return self.y - self.size/2 > SCREEN_HEIGHT

# ---------------------------
# Coin Class (+50 score)
# ---------------------------
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

# ---------------------------
# Health Pack Class (Displayed as a "+" that heals player by 50% of max health)
# ---------------------------
class HealthPack:
    def __init__(self):
        self.x = random.randint(30, SCREEN_WIDTH - 30)
        self.y = -30
        self.size = 20  # size for the plus sign
        self.speed = 100
    def update(self, dt):
        self.y += self.speed * dt
    def draw(self, surface):
        center = (int(self.x), int(self.y))
        half = self.size // 2
        pygame.draw.line(surface, GREEN, (center[0], center[1] - half), (center[0], center[1] + half), 3)
        pygame.draw.line(surface, GREEN, (center[0] - half, center[1]), (center[0] + half, center[1]), 3)
    def off_screen(self):
        return self.y - self.size > SCREEN_HEIGHT

# ---------------------------
# Global Game Objects & Initialization
# ---------------------------
player = Player()
bullets = []
enemy_bullets = []
enemies = []
asteroids = []
coins = []
healthpacks = []
explosions = []
stars = [Star() for _ in range(50)]
enemy_spawn_timer = 0
asteroid_spawn_timer = 0
coin_spawn_timer = 0
healthpack_spawn_timer = 0
boss = None

# ---------------------------
# Title Screen Function
# ---------------------------
def draw_title_screen():
    screen.fill(DARKBLUE)
    for star in stars:
        star.draw(screen)
    draw_text(screen, "Space Shooter", 60, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    start_rect = pygame.Rect(0, 0, 200, 50)
    start_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    exit_rect = pygame.Rect(0, 0, 200, 50)
    exit_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Start", start_rect, GRAY, WHITE)
    draw_button(screen, "Exit", exit_rect, GRAY, WHITE)
    return start_rect, exit_rect

# ---------------------------
# Instructions Screen (Brief text about game and controls)
# ---------------------------
def draw_instructions_screen():
    screen.fill(DARKBLUE)
    for star in stars:
        star.draw(screen)
    instructions = [
        "Welcome to Space Shooter!",
        "Use the Arrow Keys to move your spaceship.",
        "Your ship auto-fires lasers ('pew' sound) at enemies.",
        "Avoid enemy ships, asteroids, and enemy bullets.",
        "Collect coins (+50 points) and health packs (+50% health).",
        "When your score reaches 4000, you'll get a rest period",
        "to prepare for the Boss Battle. Good luck!"
    ]
    y_offset = SCREEN_HEIGHT//4
    for line in instructions:
        draw_text(screen, line, 28, WHITE, (SCREEN_WIDTH//2, y_offset))
        y_offset += 40
    draw_text(screen, "Press any key to continue...", 24, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT - 80))
    pygame.display.flip()

# ---------------------------
# Game Over Screen Function
# ---------------------------
def draw_game_over_screen():
    screen.fill(DARKBLUE)
    draw_text(screen, "Game Over", 60, RED, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    draw_text(screen, f"Score: {int(score)}", 40, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
    retry_rect = pygame.Rect(0, 0, 200, 50)
    retry_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    title_rect = pygame.Rect(0, 0, 200, 50)
    title_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Retry", retry_rect, GRAY, WHITE)
    draw_button(screen, "Title", title_rect, GRAY, WHITE)
    return retry_rect, title_rect

# ---------------------------
# Boss Victory Screen Function
# ---------------------------
def draw_boss_victory_screen():
    screen.fill(DARKBLUE)
    draw_text(screen, "Congratulations!", 60, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    draw_text(screen, "You defeated the Boss!", 40, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
    cont_rect = pygame.Rect(0, 0, 250, 50)
    title_rect = pygame.Rect(0, 0, 250, 50)
    cont_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    title_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Free Battle", cont_rect, GRAY, WHITE)
    draw_button(screen, "Title", title_rect, GRAY, WHITE)
    return cont_rect, title_rect

# ---------------------------
# Rest State Screen (Before Boss Battle)
# ---------------------------
def draw_rest_screen():
    screen.fill(DARKBLUE)
    for star in stars:
        star.draw(screen)
    message = "Prepare for Boss Battle! Rest now and collect extra Health Packs!"
    draw_text(screen, message, 36, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
    draw_text(screen, "You have been awarded bonus Health Packs!", 28, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    draw_text(screen, "Rest for a few seconds...", 28, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
    pygame.display.flip()

# ---------------------------
# Reset Game Function
# ---------------------------
def reset_game():
    global player, bullets, enemy_bullets, enemies, asteroids, coins, healthpacks, explosions, enemy_spawn_timer, asteroid_spawn_timer, coin_spawn_timer, healthpack_spawn_timer, score, boss
    player = Player()
    bullets = []
    enemy_bullets = []
    enemies = []
    asteroids = []
    coins = []
    healthpacks = []
    explosions = []
    enemy_spawn_timer = 0
    asteroid_spawn_timer = 0
    coin_spawn_timer = 0
    healthpack_spawn_timer = 0
    score = 0
    boss = None

# ---------------------------
# Main Game Loop
# ---------------------------
instructions_timer = 5.0  # 5 seconds instructions
rest_timer = 5.0         # 5 seconds rest period

running = True
# We'll use an additional state "instructions" to show game instructions after the title screen.
while running:
    dt = clock.tick(60) / 1000.0  # delta time in seconds

    if game_state == "start":
        start_button, exit_button = draw_title_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    reset_game()
                    instructions_timer = 5.0
                    game_state = "instructions"
                    pygame.mixer.music.stop()
                elif exit_button.collidepoint(event.pos):
                    running = False
        pygame.display.flip()

    elif game_state == "instructions":
        # Display instructions about the game.
        draw_instructions_screen()
        instructions_timer -= dt
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                instructions_timer = 0
        if instructions_timer <= 0:
            game_state = "playing"

    elif game_state == "playing":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        # In-game Menu button (top-right)
        menu_btn_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 40)
        if pygame.mouse.get_pressed()[0]:
            if menu_btn_rect.collidepoint(pygame.mouse.get_pos()):
                game_state = "start"
                pygame.mixer.music.play(-1)
        # Update stars
        for star in stars:
            star.update(dt)
        # Update player
        player.update(dt)
        # Update player's bullets
        for bullet in bullets:
            bullet.update(dt)
        bullets = [b for b in bullets if not b.off_screen()]
        # Update enemy bullets
        for eb in enemy_bullets:
            eb.update(dt)
        enemy_bullets = [eb for eb in enemy_bullets if not eb.off_screen()]
        # Update asteroids
        asteroid_spawn_timer -= dt
        if asteroid_spawn_timer <= 0:
            asteroid_spawn_timer = random.uniform(2.0, 4.0)
            asteroids.append(Asteroid())
        for asteroid in asteroids:
            asteroid.update(dt)
        asteroids = [a for a in asteroids if not a.off_screen()]
        # Update coins
        coin_spawn_timer -= dt
        if coin_spawn_timer <= 0:
            coin_spawn_timer = random.uniform(1.5, 3.0)
            coins.append(Coin())
        for coin in coins:
            coin.update(dt)
        coins = [c for c in coins if not c.off_screen()]
        # Update health packs
        healthpack_spawn_timer -= dt
        if healthpack_spawn_timer <= 0:
            healthpack_spawn_timer = random.uniform(15, 30)
            healthpacks.append(HealthPack())
        for hp in healthpacks:
            hp.update(dt)
        healthpacks = [hp for hp in healthpacks if not hp.off_screen()]
        # Check if score reaches 4000 -> enter Rest State (boss preparation)
        if score >= 4000 and boss is None:
            rest_timer = 5.0  # rest period duration
            game_state = "rest"
            # Optionally, give bonus health packs during rest:
            for _ in range(5):
                healthpacks.append(HealthPack())
        # Spawn regular enemies only if boss is not active
        if boss is None:
            max_enemies = min(1 + int(score / 500), 10)
            if len(enemies) < max_enemies:
                enemy_spawn_timer -= dt
                if enemy_spawn_timer <= 0:
                    enemy_spawn_timer = random.uniform(1.5, 3.0)
                    enemies.append(Enemy())
        # Update regular enemies
        for enemy in enemies:
            enemy.update(dt, player)
        enemies = [e for e in enemies if not e.off_screen()]
        # Update boss if exists
        if boss is not None:
            boss.update(dt, player)
            if boss.off_screen():
                boss = None
        # ---------------------------
        # Collision Checks
        # ---------------------------
        # Player Bullets with Regular Enemies
        for bullet in bullets[:]:
            for enemy in enemies[:]:
                dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                if dist < enemy.size:
                    if bullet in bullets:
                        bullets.remove(bullet)
                    enemy.health -= 1
                    if enemy.health <= 0:
                        explosions.append(Explosion(enemy.x, enemy.y))
                        explosion_sound.play()
                        if enemy in enemies:
                            enemies.remove(enemy)
                        score += 50
                    break
            # Player Bullets with Boss
            if boss is not None:
                dist = math.hypot(bullet.x - boss.x, bullet.y - boss.y)
                if dist < boss.size:
                    if bullet in bullets:
                        bullets.remove(bullet)
                    boss.health -= 1
                    if boss.health <= 0:
                        explosions.append(Explosion(boss.x, boss.y))
                        explosion_sound.play()
                        boss = None
                        game_state = "boss_victory"
                    break
            # Player Bullets with Asteroids
            for asteroid in asteroids[:]:
                dist = math.hypot(bullet.x - asteroid.x, bullet.y - asteroid.y)
                if dist < asteroid.size/2 + bullet.radius:
                    if bullet in bullets:
                        bullets.remove(bullet)
                    explosions.append(Explosion(asteroid.x, asteroid.y))
                    explosion_sound.play()
                    if asteroid in asteroids:
                        asteroids.remove(asteroid)
                    score += 50
                    break
        # Player collecting Coins
        for coin in coins[:]:
            dist = math.hypot(player.x - coin.x, player.y - coin.y)
            if dist < player.size + coin.radius:
                coins.remove(coin)
                score += 50
        # Player collecting Health Packs (heal 50% of max health)
        for hp in healthpacks[:]:
            dist = math.hypot(player.x - hp.x, player.y - hp.y)
            if dist < player.size + hp.size/2:
                heal_amount = player.max_health * 0.50
                player.health = min(player.max_health, player.health + heal_amount)
                healthpacks.remove(hp)
        # Enemy Bullets with Player
        for eb in enemy_bullets[:]:
            dist = math.hypot(player.x - eb.x, player.y - eb.y)
            if dist < player.size + eb.radius:
                player.health -= player.max_health * 0.10
                if eb in enemy_bullets:
                    enemy_bullets.remove(eb)
                if player.health <= 0:
                    game_state = "game_over"
        # Regular Enemy collision with Player
        for enemy in enemies[:]:
            dist = math.hypot(player.x - enemy.x, player.y - enemy.y)
            if dist < player.size + enemy.size:
                player.health -= player.max_health * 0.25
                explosions.append(Explosion(enemy.x, enemy.y))
                explosion_sound.play()
                if enemy in enemies:
                    enemies.remove(enemy)
                if player.health <= 0:
                    game_state = "game_over"
        # Asteroid collision with Player
        for asteroid in asteroids[:]:
            rect = pygame.Rect(asteroid.x - asteroid.size/2, asteroid.y - asteroid.size/2, asteroid.size, asteroid.size)
            player_rect = pygame.Rect(player.x - player.size, player.y - player.size, player.size*2, player.size*2)
            if rect.colliderect(player_rect):
                player.health -= player.max_health * 0.15
                explosions.append(Explosion(asteroid.x, asteroid.y))
                explosion_sound.play()
                if asteroid in asteroids:
                    asteroids.remove(asteroid)
                if player.health <= 0:
                    game_state = "game_over"
        # Increase score over time
        score += dt * 5
        # Update explosions
        for exp in explosions[:]:
            exp.update(dt)
            if exp.timer <= 0:
                explosions.remove(exp)
        # ---------------------------
        # Drawing
        # ---------------------------
        screen.fill(BLACK)
        for star in stars:
            star.draw(screen)
        for asteroid in asteroids:
            asteroid.draw(screen)
        for coin in coins:
            coin.draw(screen)
        for hp in healthpacks:
            hp.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        if boss is not None:
            boss.draw(screen)
        for eb in enemy_bullets:
            eb.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)
        for exp in explosions:
            exp.draw(screen)
        player.draw(screen)
        draw_text(screen, f"Score: {int(score)}", 24, WHITE, (70, 20))
        pygame.draw.rect(screen, RED, (20, 40, 100, 10))
        pygame.draw.rect(screen, GREEN, (20, 40, int(100 * (player.health/player.max_health)), 10))
        draw_button(screen, "Menu", menu_btn_rect, DARKBLUE, WHITE)
        if score >= 3900 and boss is None:
            draw_text(screen, "Boss Incoming Soon! Rest and collect extra Health Packs!", 40, YELLOW, (SCREEN_WIDTH//2, 80))
        pygame.display.flip()

    elif game_state == "rest":
        # Rest state before boss battle: let player collect extra health packs
        draw_rest_screen()
        rest_timer -= dt
        if rest_timer <= 0:
            game_state = "playing"
            # Spawn boss now after rest period
            boss = BossEnemy()
            enemies = []
            enemy_bullets = []
        # During rest, continue spawning health packs at a higher rate
        healthpack_spawn_timer -= dt * 2  # double frequency during rest
        if healthpack_spawn_timer <= 0:
            healthpack_spawn_timer = random.uniform(5, 8)
            healthpacks.append(HealthPack())
        pygame.display.flip()

    elif game_state == "boss_victory":
        cont_btn, title_btn = draw_boss_victory_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if cont_btn.collidepoint(event.pos):
                    game_state = "playing"
                    score = 0  # Reset score so boss doesn't trigger again
                elif title_btn.collidepoint(event.pos):
                    game_state = "start"
                    pygame.mixer.music.play(-1)
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
                    pygame.mixer.music.play(-1)
        pygame.display.flip()

pygame.quit()
sys.exit()
