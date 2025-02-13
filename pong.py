import pygame, sys, random, numpy as np

# ============================
# Initialization & Fullscreen Setup
# ============================
pygame.init()
pygame.mixer.init()  # Initialize the mixer
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
# Create a fullscreen window:
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Retro Pong")
clock = pygame.time.Clock()

# ============================
# Colors & Global Variables
# ============================
WHITE    = (255, 255, 255)
BLACK    = (0, 0, 0)
GRAY     = (100, 100, 100)
DARKGRAY = (50, 50, 50)
RED      = (220, 20, 60)
GREEN    = (50, 205, 50)
BLUE     = (50, 150, 255)
YELLOW   = (255, 215, 0)

# Game States: "title", "difficulty_select", "playing", "game_over"
state = "title"
mode = None           # "bot" or "pvp"
bot_difficulty = None # Selected difficulty string
winner = None         # "Left" or "Right" when game ends

WIN_SCORE = 10  # Winning score

# ============================
# Utility Functions
# ============================
def draw_text(surf, text, size, color, center):
    font = pygame.font.SysFont("arial", size)
    txt_surface = font.render(text, True, color)
    txt_rect = txt_surface.get_rect(center=center)
    surf.blit(txt_surface, txt_rect)

def draw_button(surf, text, rect, button_color, text_color):
    pygame.draw.rect(surf, button_color, rect)
    pygame.draw.rect(surf, WHITE, rect, 2)
    draw_text(surf, text, 24, text_color, rect.center)

# ============================
# Sound Generation (Stereo, No Local Assets)
# ============================
def generate_sound(frequency, duration, volume=1.0, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Generate a sine wave
    wave = np.sin(2 * np.pi * frequency * t)
    # Scale to int16 range
    wave = (wave * 32767 * volume).astype(np.int16)
    # Convert mono to stereo by duplicating channels
    stereo_wave = np.column_stack((wave, wave))
    sound = pygame.sndarray.make_sound(stereo_wave)
    return sound

# Generate the sounds:
tuk_sound = generate_sound(frequency=700, duration=0.05, volume=0.8)
plop_sound = generate_sound(frequency=300, duration=0.1, volume=0.8)

# ============================
# Game Object Classes
# ============================
class Paddle:
    def __init__(self, x, y):
        self.width = 20
        self.height = 100
        self.x = x
        self.y = y
        self.speed = 400  # Paddle speed in pixels per second

    def update(self, dt, up_key, down_key):
        keys = pygame.key.get_pressed()
        if keys[up_key]:
            self.y -= self.speed * dt
        if keys[down_key]:
            self.y += self.speed * dt
        # Keep paddle within screen bounds
        if self.y < 0:
            self.y = 0
        if self.y + self.height > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.height

    def auto_update(self, dt, ball, reaction_speed):
        # Simple AI: move paddle toward the ball's y position
        target = ball.y - self.height/2 + ball.height/2
        if self.y + self.height/2 < target:
            self.y += reaction_speed * dt
        elif self.y + self.height/2 > target:
            self.y -= reaction_speed * dt
        # Clamp paddle position
        if self.y < 0:
            self.y = 0
        if self.y + self.height > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.height

    def draw(self, surf):
        pygame.draw.rect(surf, WHITE, (int(self.x), int(self.y), self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Ball:
    def __init__(self):
        self.width = 20
        self.height = 20
        self.reset()

    def reset(self):
        # Reset ball to center and update speed based on total score.
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2
        base_speed = 400 + (left_score + right_score) * 20
        self.vx = random.choice([-1, 1]) * base_speed
        self.vy = random.choice([-1, 1]) * base_speed

    def update(self, dt, left_paddle, right_paddle):
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bounce off top and bottom
        if self.y <= 0:
            self.y = 0
            self.vy = -self.vy
        if self.y + self.height >= SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.height
            self.vy = -self.vy

        ball_rect = self.get_rect()
        # Check collision with left paddle
        if ball_rect.colliderect(left_paddle.get_rect()):
            self.x = left_paddle.x + left_paddle.width
            self.vx = -self.vx
            tuk_sound.play()
        # Check collision with right paddle
        if ball_rect.colliderect(right_paddle.get_rect()):
            self.x = right_paddle.x - self.width
            self.vx = -self.vx
            tuk_sound.play()

    def draw(self, surf):
        pygame.draw.rect(surf, YELLOW, (int(self.x), int(self.y), self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# ============================
# Global Game Variables for Playing State
# ============================
left_score = 0
right_score = 0
left_paddle = None
right_paddle = None
ball = None
# Bot reaction speed (adjustable via difficulty)
bot_reaction = 200  # default value; changes with difficulty

def init_play():
    global left_paddle, right_paddle, ball, left_score, right_score
    left_score = 0
    right_score = 0
    paddle_margin = 30
    left_paddle = Paddle(paddle_margin, SCREEN_HEIGHT//2 - 50)
    right_paddle = Paddle(SCREEN_WIDTH - paddle_margin - 20, SCREEN_HEIGHT//2 - 50)
    ball_obj = Ball()
    return ball_obj

# ============================
# Menu Screens
# ============================
def title_screen():
    screen.fill(BLACK)
    draw_text(screen, "Retro Pong", 80, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    play_bot_rect = pygame.Rect(0, 0, 300, 50)
    play_pvp_rect = pygame.Rect(0, 0, 300, 50)
    exit_rect = pygame.Rect(0, 0, 300, 50)
    play_bot_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    play_pvp_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    exit_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 140)
    draw_button(screen, "Play vs Bot", play_bot_rect, DARKGRAY, WHITE)
    draw_button(screen, "Play vs Player", play_pvp_rect, DARKGRAY, WHITE)
    draw_button(screen, "Exit", exit_rect, DARKGRAY, WHITE)
    return play_bot_rect, play_pvp_rect, exit_rect

def difficulty_screen():
    screen.fill(BLACK)
    draw_text(screen, "Select Bot Difficulty", 80, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    btn_width = 250
    btn_height = 50
    spacing = 20
    total = 4 * btn_height + 3 * spacing
    start_y = SCREEN_HEIGHT//2 - total//2
    easy_rect = pygame.Rect(0, 0, btn_width, btn_height)
    medium_rect = pygame.Rect(0, 0, btn_width, btn_height)
    hard_rect = pygame.Rect(0, 0, btn_width, btn_height)
    very_rect = pygame.Rect(0, 0, btn_width, btn_height)
    easy_rect.center = (SCREEN_WIDTH//2, start_y + btn_height//2)
    medium_rect.center = (SCREEN_WIDTH//2, start_y + btn_height + spacing + btn_height//2)
    hard_rect.center = (SCREEN_WIDTH//2, start_y + 2*(btn_height+spacing) + btn_height//2)
    very_rect.center = (SCREEN_WIDTH//2, start_y + 3*(btn_height+spacing) + btn_height//2)
    draw_button(screen, "Easy", easy_rect, DARKGRAY, WHITE)
    draw_button(screen, "Medium", medium_rect, DARKGRAY, WHITE)
    draw_button(screen, "Hard", hard_rect, DARKGRAY, WHITE)
    draw_button(screen, "Very Hard", very_rect, DARKGRAY, WHITE)
    return easy_rect, medium_rect, hard_rect, very_rect

def win_screen(winner_side):
    screen.fill(BLACK)
    draw_text(screen, f"{winner_side} Player Wins!", 80, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
    draw_text(screen, f"Score: {left_score} - {right_score}", 50, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 70))
    retry_rect = pygame.Rect(0, 0, 300, 50)
    title_rect = pygame.Rect(0, 0, 300, 50)
    retry_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    title_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70)
    draw_button(screen, "Retry", retry_rect, DARKGRAY, WHITE)
    draw_button(screen, "Title", title_rect, DARKGRAY, WHITE)
    return retry_rect, title_rect

# ============================
# Main Game Loop
# ============================
ball = None
left_score = 0
right_score = 0

running = True
while running:
    dt = clock.tick(60) / 1000.0  # Delta time in seconds

    if state == "title":
        play_bot_btn, play_pvp_btn, exit_btn = title_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_bot_btn.collidepoint(event.pos):
                    mode = "bot"
                    state = "difficulty_select"
                elif play_pvp_btn.collidepoint(event.pos):
                    mode = "pvp"
                    state = "playing"
                    ball = init_play()
                elif exit_btn.collidepoint(event.pos):
                    running = False
        pygame.display.flip()

    elif state == "difficulty_select":
        easy_btn, med_btn, hard_btn, very_btn = difficulty_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_btn.collidepoint(event.pos):
                    bot_difficulty = "Easy"
                    bot_reaction = 150
                    state = "playing"
                    ball = init_play()
                elif med_btn.collidepoint(event.pos):
                    bot_difficulty = "Medium"
                    bot_reaction = 250
                    state = "playing"
                    ball = init_play()
                elif hard_btn.collidepoint(event.pos):
                    bot_difficulty = "Hard"
                    bot_reaction = 350
                    state = "playing"
                    ball = init_play()
                elif very_btn.collidepoint(event.pos):
                    bot_difficulty = "Very Hard"
                    bot_reaction = 500  # nearly perfect tracking
                    state = "playing"
                    ball = init_play()
        pygame.display.flip()

    elif state == "playing":
        # Add a Title button in the upper-right corner.
        title_btn_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if title_btn_rect.collidepoint(event.pos):
                    state = "title"

        # Update paddles:
        left_paddle.update(dt, pygame.K_w, pygame.K_s)
        if mode == "pvp":
            right_paddle.update(dt, pygame.K_UP, pygame.K_DOWN)
        else:
            right_paddle.auto_update(dt, ball, bot_reaction)

        # Update ball:
        ball.update(dt, left_paddle, right_paddle)

        # Scoring: if ball goes off screen, play plop sound and reset.
        if ball.x < 0:
            right_score += 1
            plop_sound.play()
            ball.reset()
        if ball.x + ball.width > SCREEN_WIDTH:
            left_score += 1
            plop_sound.play()
            ball.reset()

        # Win condition:
        if left_score >= WIN_SCORE:
            winner = "Left"
            state = "game_over"
        elif right_score >= WIN_SCORE:
            winner = "Right"
            state = "game_over"

        # Draw playing screen:
        screen.fill(BLACK)
        # Draw center net:
        net_width = 4
        net_rect = pygame.Rect(SCREEN_WIDTH//2 - net_width//2, 0, net_width, SCREEN_HEIGHT)
        pygame.draw.rect(screen, WHITE, net_rect)
        # Draw paddles and ball:
        left_paddle.draw(screen)
        right_paddle.draw(screen)
        ball.draw(screen)
        # Draw scores:
        draw_text(screen, f"{left_score}", 50, WHITE, (SCREEN_WIDTH//4, 50))
        draw_text(screen, f"{right_score}", 50, WHITE, (SCREEN_WIDTH*3//4, 50))
        # Draw Title button:
        draw_button(screen, "Title", title_btn_rect, DARKGRAY, WHITE)
        pygame.display.flip()

    elif state == "game_over":
        retry_btn, title_btn = win_screen(winner)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_btn.collidepoint(event.pos):
                    ball = init_play()
                    left_score = 0
                    right_score = 0
                    state = "playing"
                elif title_btn.collidepoint(event.pos):
                    state = "title"
        pygame.display.flip()

pygame.quit()
sys.exit()
