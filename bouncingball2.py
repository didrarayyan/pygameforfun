import pygame
import math

# Initialize Pygame
pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Ball in Spinning Square")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Square properties
square_center = (width//2, height//2)
square_size = 300
square_angle = 0
rotation_speed = 1  # Degrees per frame

# Ball properties
ball_radius = 10
ball_pos = [width//2, height//2 - 100]  # Initial position
ball_vel = [0, 0]
gravity = 0.2
damping = 0.8

# Main loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update square angle
    square_angle += rotation_speed
    square_angle_rad = math.radians(square_angle)

    # Apply gravity
    ball_vel[1] += gravity

    # Update ball position
    ball_pos[0] += ball_vel[0]
    ball_pos[1] += ball_vel[1]

    # Collision detection with rotating square
    bx = ball_pos[0] - square_center[0]
    by = ball_pos[1] - square_center[1]

    # Rotate ball position to square's local coordinates
    cos_angle = math.cos(-square_angle_rad)
    sin_angle = math.sin(-square_angle_rad)
    tx = bx * cos_angle - by * sin_angle
    ty = bx * sin_angle + by * cos_angle

    s_half = square_size / 2
    collision = False
    new_tx, new_ty = tx, ty

    # Check collisions with all edges
    if tx - ball_radius < -s_half:
        new_tx = -s_half + ball_radius
        collision = True
    elif tx + ball_radius > s_half:
        new_tx = s_half - ball_radius
        collision = True

    if ty - ball_radius < -s_half:
        new_ty = -s_half + ball_radius
        collision = True
    elif ty + ball_radius > s_half:
        new_ty = s_half - ball_radius
        collision = True

    if collision:
        # Adjust position in world coordinates
        cos_rot = math.cos(square_angle_rad)
        sin_rot = math.sin(square_angle_rad)
        new_bx = new_tx * cos_rot - new_ty * sin_rot
        new_by = new_tx * sin_rot + new_ty * cos_rot
        ball_pos[0] = square_center[0] + new_bx
        ball_pos[1] = square_center[1] + new_by

        # Adjust velocity
        vx, vy = ball_vel
        # Convert velocity to local coordinates
        local_vx = vx * cos_rot + vy * sin_rot
        local_vy = -vx * sin_rot + vy * cos_rot

        # Reverse appropriate components
        if tx - ball_radius < -s_half or tx + ball_radius > s_half:
            local_vx *= -damping
        if ty - ball_radius < -s_half or ty + ball_radius > s_half:
            local_vy *= -damping

        # Convert back to world coordinates
        ball_vel[0] = local_vx * cos_rot - local_vy * sin_rot
        ball_vel[1] = local_vx * sin_rot + local_vy * cos_rot

    # Draw everything
    screen.fill(WHITE)

    # Draw rotating square
    square_surface = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
    pygame.draw.rect(square_surface, BLACK, (0, 0, square_size, square_size), 2)
    rotated_square = pygame.transform.rotate(square_surface, square_angle)
    rotated_rect = rotated_square.get_rect(center=square_center)
    screen.blit(rotated_square, rotated_rect.topleft)

    # Draw ball
    pygame.draw.circle(screen, RED, (int(ball_pos[0]), int(ball_pos[1])), ball_radius)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()