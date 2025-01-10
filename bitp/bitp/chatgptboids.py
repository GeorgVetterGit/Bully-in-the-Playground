import pygame
import random
import math

# Bildschirmkonfiguration
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (30, 30, 30)

# Boid-Konfiguration
NUM_BOIDS = 100
MAX_SPEED = 4
MAX_FORCE = 0.1
PERCEPTION_RADIUS = 50
PREDATOR_RADIUS = 100

# Farben
BOID_COLOR = (200, 200, 255)
PREDATOR_COLOR = (255, 100, 100)

# Pygame initialisieren
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Boids Simulation")
clock = pygame.time.Clock()

class Boid:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
        self.acceleration = pygame.Vector2(0, 0)

    def edges(self):
        if self.position.x > WIDTH:
            self.position.x = 0
        elif self.position.x < 0:
            self.position.x = WIDTH

        if self.position.y > HEIGHT:
            self.position.y = 0
        elif self.position.y < 0:
            self.position.y = HEIGHT

    def apply_force(self, force):
        self.acceleration += force

    def update(self):
        self.velocity += self.acceleration
        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)
        self.position += self.velocity
        self.acceleration *= 0

    def show(self):
        pygame.draw.circle(screen, BOID_COLOR, (int(self.position.x), int(self.position.y)), 3)

    def align(self, boids):
        steering = pygame.Vector2()
        total = 0
        for boid in boids:
            if self.position.distance_to(boid.position) < PERCEPTION_RADIUS:
                steering += boid.velocity
                total += 1
        if total > 0:
            steering /= total
            steering = steering.normalize() * MAX_SPEED
            steering -= self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def cohesion(self, boids):
        steering = pygame.Vector2()
        total = 0
        for boid in boids:
            if self.position.distance_to(boid.position) < PERCEPTION_RADIUS:
                steering += boid.position
                total += 1
        if total > 0:
            steering /= total
            steering -= self.position
            if steering.length() > MAX_SPEED:
                steering.scale_to_length(MAX_SPEED)
            steering -= self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def separation(self, boids):
        steering = pygame.Vector2()
        total = 0
        for boid in boids:
            distance = self.position.distance_to(boid.position)
            if distance < PERCEPTION_RADIUS and distance > 0:
                diff = self.position - boid.position
                diff /= distance
                steering += diff
                total += 1
        if total > 0:
            steering /= total
            if steering.length() > MAX_SPEED:
                steering.scale_to_length(MAX_SPEED)
            steering -= self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def avoid_predator(self, predator):
        steering = pygame.Vector2()
        distance = self.position.distance_to(predator)
        if distance < PREDATOR_RADIUS:
            diff = self.position - predator
            diff /= distance
            steering += diff
            if steering.length() > MAX_SPEED:
                steering.scale_to_length(MAX_SPEED)
            steering -= self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def flock(self, boids, predator):
        alignment = self.align(boids)
        cohesion = self.cohesion(boids)
        separation = self.separation(boids)
        avoidance = self.avoid_predator(predator)

        # Gewichtung der Regeln
        self.apply_force(alignment * 1.0)
        self.apply_force(cohesion * 1.0)
        self.apply_force(separation * 1.5)
        self.apply_force(avoidance * 2.0)

# Boids erstellen
boids = [Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_BOIDS)]

# Predator erstellen
predator = pygame.Vector2(WIDTH // 2, HEIGHT // 2)

# Hauptprogramm
running = True
while running:
    screen.fill(BACKGROUND_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Predator-Position aktualisieren (Maus folgt)
    mouse_pos = pygame.mouse.get_pos()
    predator.update(mouse_pos)

    for boid in boids:
        boid.edges()
        boid.flock(boids, predator)
        boid.update()
        boid.show()

    # Predator anzeigen
    pygame.draw.circle(screen, PREDATOR_COLOR, (int(predator.x), int(predator.y)), 8)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
