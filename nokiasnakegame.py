import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# --- Configuration ---
# Grid settings (each cell will be a square of CELL_SIZE x CELL_SIZE pixels)
CELL_SIZE = 20
GRID_WIDTH = 30   # number of cells horizontally
GRID_HEIGHT = 20  # number of cells vertically

WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Nokia Snake Game")
clock = pygame.time.Clock()

# Colors
BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GREEN      = (0, 255, 0)
DARK_GREEN = (0, 155, 0)
RED        = (255, 0, 0)
GRAY       = (40, 40, 40)

# Game states: "start", "playing", "game_over", "win"
game_state = "start"

# Snake movement delay (in milliseconds)
MOVE_DELAY = 150

# Global game variables (will be initialized in reset_game)
snake = []         # list of (x,y) tuples representing snake segments; head is snake[0]
direction = (1, 0) # current movement direction as (dx, dy)
food = None        # current food position (x, y)
last_move_time = 0

# --- Helper Functions ---
def draw_text(surface, text, size, color, center):
    """Draws centered text on a surface."""
    font = pygame.font.SysFont("Arial", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    surface.blit(text_surface, text_rect)

def draw_button(surface, text, rect, button_color, text_color):
    """Draws a button (rectangle with text)."""
    pygame.draw.rect(surface, button_color, rect)
    pygame.draw.rect(surface, WHITE, rect, 2)  # border
    font = pygame.font.SysFont("Arial", 24)
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

def get_random_food_position():
    """Returns a random cell that is not occupied by the snake.
       Returns None if no cell is available (win condition)."""
    available = []
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            if (x, y) not in snake:
                available.append((x, y))
    return random.choice(available) if available else None

def reset_game():
    """Resets the game variables to start a new game."""
    global snake, direction, food, last_move_time, game_state
    # Start in the middle of the grid; initial snake has 3 segments.
    start_x = GRID_WIDTH // 2
    start_y = GRID_HEIGHT // 2
    snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
    direction = (1, 0)  # moving to the right
    food_pos = get_random_food_position()
    food = food_pos  # may be None if grid is full (won)
    last_move_time = pygame.time.get_ticks()
    game_state = "playing"

# --- Main Game Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # --- Menu Event Handling ---
        if game_state == "start":
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Define the start button rectangle.
                start_button_rect = pygame.Rect(0, 0, 200, 50)
                start_button_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                if start_button_rect.collidepoint(event.pos):
                    reset_game()

        elif game_state in ("game_over", "win"):
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Define the retry and exit buttons.
                retry_button_rect = pygame.Rect(0, 0, 150, 50)
                retry_button_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                exit_button_rect = pygame.Rect(0, 0, 150, 50)
                exit_button_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70)
                if retry_button_rect.collidepoint(event.pos):
                    reset_game()
                elif exit_button_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        # --- Playing State Event Handling ---
        elif game_state == "playing":
            if event.type == pygame.KEYDOWN:
                # Update direction based on arrow keys; disallow direct reversal.
                if event.key == pygame.K_UP and direction != (0, 1):
                    direction = (0, -1)
                elif event.key == pygame.K_DOWN and direction != (0, -1):
                    direction = (0, 1)
                elif event.key == pygame.K_LEFT and direction != (1, 0):
                    direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and direction != (-1, 0):
                    direction = (1, 0)

    # --- Game Logic ---
    if game_state == "playing":
        current_time = pygame.time.get_ticks()
        if current_time - last_move_time > MOVE_DELAY:
            # Compute new head position.
            new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
            # Check collision with walls.
            if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
                game_state = "game_over"
            # Check collision with self.
            elif new_head in snake:
                game_state = "game_over"
            else:
                # Move the snake: add the new head.
                snake.insert(0, new_head)
                # Check if food is eaten.
                if new_head == food:
                    food = get_random_food_position()
                    # If no food can be placed, the grid is full => win!
                    if food is None:
                        game_state = "win"
                else:
                    # Remove tail segment.
                    snake.pop()
            last_move_time = current_time

    # --- Drawing ---
    screen.fill(BLACK)

    if game_state == "start":
        # Draw the title and start button.
        draw_text(screen, "Snake Game", 48, WHITE, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4))
        start_button_rect = pygame.Rect(0, 0, 200, 50)
        start_button_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        draw_button(screen, "Start", start_button_rect, DARK_GREEN, WHITE)

    elif game_state == "playing":
        # Optionally, draw grid lines for a retro look.
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (0, y), (WINDOW_WIDTH, y))

        # Draw the snake (each segment as a green cell).
        for segment in snake:
            rect = pygame.Rect(segment[0] * CELL_SIZE, segment[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, GREEN, rect)

        # Draw the food (a red cell).
        if food:
            food_rect = pygame.Rect(food[0] * CELL_SIZE, food[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, RED, food_rect)

    elif game_state in ("game_over", "win"):
        # Draw game over or win message and show Retry/Exit buttons.
        if game_state == "game_over":
            draw_text(screen, "Game Over", 48, RED, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4))
        else:
            draw_text(screen, "You Win!", 48, GREEN, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4))
        retry_button_rect = pygame.Rect(0, 0, 150, 50)
        retry_button_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        exit_button_rect = pygame.Rect(0, 0, 150, 50)
        exit_button_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70)
        draw_button(screen, "Retry", retry_button_rect, DARK_GREEN, WHITE)
        draw_button(screen, "Exit", exit_button_rect, DARK_GREEN, WHITE)

    pygame.display.flip()
    clock.tick(60)
