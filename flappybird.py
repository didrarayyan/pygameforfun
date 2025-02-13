import pygame
import random
import sys

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Flappy Bird (Lines Only)")
clock = pygame.time.Clock()

# --------------------
# Bird parameters
# --------------------
bird_x = 150                     # fixed horizontal position
bird_y = HEIGHT // 2             # starting vertical position
bird_radius = 10                 # radius of the bird (drawn as an outlined circle)
bird_velocity = 0                # vertical velocity (pixels/second)
gravity = 500                    # gravitational acceleration (pixels/s^2)
jump_impulse = -200              # upward impulse when UP is pressed
down_impulse = 200               # downward impulse when DOWN is pressed

# --------------------
# Pipe parameters
# --------------------
pipe_width = 80                  # width of the pipes
pipe_gap = 150                   # vertical gap between top and bottom pipe segments
pipe_speed = 200                 # speed at which pipes move left (pixels/second)
pipe_interval = 1500             # time (ms) between new pipes
last_pipe_time = pygame.time.get_ticks()
pipes = []                       # each pipe is a dict with keys: 'x' and 'gap_y'

def add_pipe():
    """Adds a new pipe with a random gap position."""
    gap_y = random.randint(100, HEIGHT - 100 - pipe_gap)
    pipe = {'x': WIDTH, 'gap_y': gap_y, 'scored': False}
    pipes.append(pipe)

def check_collision():
    """Check for collisions between the bird and the pipes or screen edges."""
    # Check if the bird goes off the top or bottom of the screen.
    if bird_y - bird_radius < 0 or bird_y + bird_radius > HEIGHT:
        return True

    # Define a rectangle around the bird for collision detection.
    bird_rect = pygame.Rect(bird_x - bird_radius, bird_y - bird_radius,
                            bird_radius * 2, bird_radius * 2)
    for pipe in pipes:
        # Top pipe rectangle: from the top of the screen down to the gap.
        top_rect = pygame.Rect(pipe['x'], 0, pipe_width, pipe['gap_y'])
        # Bottom pipe rectangle: from the bottom of the gap to the bottom of the screen.
        bottom_rect = pygame.Rect(pipe['x'], pipe['gap_y'] + pipe_gap,
                                  pipe_width, HEIGHT - (pipe['gap_y'] + pipe_gap))
        if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
            return True
    return False

score = 0

# --------------------
# Main Game Loop
# --------------------
running = True
while running:
    dt = clock.tick(60) / 1000.0  # Delta time in seconds (aiming for 60 FPS)

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # On key press, apply an impulse to the bird.
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                bird_velocity = jump_impulse
            if event.key == pygame.K_DOWN:
                bird_velocity = down_impulse

    # --- Update Bird ---
    bird_velocity += gravity * dt
    bird_y += bird_velocity * dt

    # --- Update Pipes ---
    # Move each pipe to the left.
    for pipe in pipes:
        pipe['x'] -= pipe_speed * dt

    # Remove pipes that have moved off screen.
    pipes = [pipe for pipe in pipes if pipe['x'] + pipe_width > 0]

    # Add new pipes at regular intervals.
    current_time = pygame.time.get_ticks()
    if current_time - last_pipe_time > pipe_interval:
        add_pipe()
        last_pipe_time = current_time

    # Increase score if the bird passes a pipe.
    for pipe in pipes:
        if not pipe['scored'] and pipe['x'] + pipe_width < bird_x:
            score += 1
            pipe['scored'] = True

    # --- Check for Collisions ---
    if check_collision():
        print("Game Over! Your score:", score)
        running = False

    # --- Drawing ---
    # Clear screen (sky blue background)
    screen.fill((135, 206, 235))

    # Draw pipes as outlined rectangles (using lines)
    for pipe in pipes:
        top_rect = pygame.Rect(pipe['x'], 0, pipe_width, pipe['gap_y'])
        bottom_rect = pygame.Rect(pipe['x'], pipe['gap_y'] + pipe_gap,
                                  pipe_width, HEIGHT - (pipe['gap_y'] + pipe_gap))
        pygame.draw.rect(screen, (34, 139, 34), top_rect, 2)
        pygame.draw.rect(screen, (34, 139, 34), bottom_rect, 2)

    # Draw the bird as an outlined circle.
    pygame.draw.circle(screen, (255, 255, 0), (int(bird_x), int(bird_y)), bird_radius, 2)

    # Draw a ground line at the bottom.
    pygame.draw.line(screen, (139, 69, 19), (0, HEIGHT), (WIDTH, HEIGHT), 4)

    # Draw the score.
    font = pygame.font.SysFont(None, 36)
    score_surface = font.render(f"Score: {score}", True, (0, 0, 0))
    screen.blit(score_surface, (10, 10))

    # Update the display.
    pygame.display.flip()

pygame.quit()
sys.exit()
