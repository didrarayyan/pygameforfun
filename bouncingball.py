import pygame
import math

# Initialize Pygame
pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Ball in a Spinning Square")
clock = pygame.time.Clock()

# Simulation parameters
c = pygame.math.Vector2(width / 2, height / 2)  # Center of the square (and screen)
L = 300             # Side length of the square (in pixels)
half_L = L / 2.0
ball_radius = 10    # Radius of the ball
# Start the ball a little offset from the center
p = c + pygame.math.Vector2(50, -50)  # ball position (world coordinates)
v = pygame.math.Vector2(150, -200)    # ball velocity (pixels per second)
gravity = pygame.math.Vector2(0, 500)   # gravity acceleration (pixels/s²)

theta = 0.0         # initial rotation angle of the square (radians)
omega = 0.5         # angular velocity of the square (radians per second)

def draw_square(center, angle, side, color=(200, 200, 200), width=2):
    """Draws a square of given side length, rotated by angle (radians)."""
    half_side = side / 2.0
    # Define the four corners in local coordinates (centered at (0,0))
    local_corners = [
        pygame.math.Vector2(-half_side, -half_side),
        pygame.math.Vector2( half_side, -half_side),
        pygame.math.Vector2( half_side,  half_side),
        pygame.math.Vector2(-half_side,  half_side)
    ]
    # Rotate each corner and translate to the world center
    world_corners = []
    for corner in local_corners:
        # rotate_rad rotates the vector by the given angle in radians (counterclockwise)
        rotated = corner.rotate_rad(angle)
        world = center + rotated
        world_corners.append((world.x, world.y))
    pygame.draw.polygon(screen, color, world_corners, width)

running = True
while running:
    dt = clock.tick(60) / 1000.0  # time step in seconds (aiming at 60 FPS)
    
    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Update physics in world coordinates ---
    # Apply gravity and update ball's position
    v += gravity * dt
    p += v * dt

    # Update the square’s rotation angle
    theta += omega * dt

    # --- Collision Detection in the Square’s Local Frame ---
    # Convert ball position to the square’s local coordinates.
    # In local coordinates, the square is axis-aligned with boundaries at ±half_L.
    q = (p - c).rotate_rad(-theta)
    # When the square rotates, the local (noninertial) ball velocity is:
    #   q_dot = R(-theta)*v + omega*(q_y, -q_x)
    # (The second term accounts for the fact that the square’s local frame is rotating.)
    q_dot = v.rotate_rad(-theta) + omega * pygame.math.Vector2(q.y, -q.x)

    collided = False
    # Check collision with left wall
    if q.x - ball_radius < -half_L:
        q.x = -half_L + ball_radius
        q_dot.x = -q_dot.x
        collided = True
    # Right wall
    if q.x + ball_radius > half_L:
        q.x = half_L - ball_radius
        q_dot.x = -q_dot.x
        collided = True
    # Top wall
    if q.y - ball_radius < -half_L:
        q.y = -half_L + ball_radius
        q_dot.y = -q_dot.y
        collided = True
    # Bottom wall
    if q.y + ball_radius > half_L:
        q.y = half_L - ball_radius
        q_dot.y = -q_dot.y
        collided = True

    # If a collision occurred, update the ball’s world position and velocity
    if collided:
        # To recover the world velocity from the corrected local velocity:
        #   v = R(theta) * [q_dot - omega*(q_y, -q_x)]
        v = (q_dot - omega * pygame.math.Vector2(q.y, -q.x)).rotate_rad(theta)
        p = c + q.rotate_rad(theta)

    # --- Drawing ---
    screen.fill((30, 30, 30))  # dark background

    # Draw the rotating square
    draw_square(c, theta, L)

    # Draw the ball
    pygame.draw.circle(screen, (255, 100, 100), (int(p.x), int(p.y)), ball_radius)

    pygame.display.flip()

pygame.quit()
