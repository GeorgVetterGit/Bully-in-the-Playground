import pygame
import numpy as np
import random
import asyncio

#TODO: Hindernisse einbauen
#TODO: Boids dürfen sich nicht überlagern
#TODO: Boids sollen am Bildschirmrand ausweichen und nicht stehen bleiben
#TODO: Bewegung schneller und mehr Schwarm. Abgleich mit Literatur und anderen Implementierungen

pygame.init() 

COLORS = {'BLACK': (0, 0, 0),
         'WHITE': (255, 255, 255),
         'RED': (255, 0, 0),
         'GRAY': (230, 230, 230)}

WIDTH = int(1280 / 1)
HEIGHT = int(720 / 1)
SWARM_SIZE = 200

def init_params():
    NUM_BULLIES = 1
    BULLY_SPEED = 1
    SWARM_SPEED = 2
    RADIUS = 50
    PREDATOR_RADIUS = 100
    SWARM_FORCE = 0.2

    PARAMETERS = {'Num Bullies': NUM_BULLIES,
                'Bully Speed': BULLY_SPEED,
                'Swarm Speed': SWARM_SPEED,
                'Swarm Radius': RADIUS,
                'Bully Radius': PREDATOR_RADIUS,
                'Swarm Force': SWARM_FORCE,
                'Allignment': 1.5,
                'Cohesion': 1.0,
                'Seperation': 2.0,
                'Avoidance': 2.0}
    return PARAMETERS

PARAMETERS = init_params()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

pygame.display.set_caption('Bully in the Playground')

PATH_KID = 'bitp/assets/kid.png'
IMG_KID = pygame.image.load(PATH_KID).convert_alpha()
IMG_KID = pygame.transform.scale(IMG_KID,(15,15))

PATH_BULLY = 'bitp/assets/bully.png'
IMG_BULLY = pygame.image.load(PATH_BULLY).convert_alpha()
IMG_BULLY = pygame.transform.scale(IMG_BULLY, (20,30))

PATH_LEFT_ARROW = 'bitp/assets/left_arrow.png'
IMG_LEFT_ARROW = pygame.image.load(PATH_LEFT_ARROW).convert_alpha()
IMG_LEFT_ARROW = pygame.transform.scale(IMG_LEFT_ARROW, (10,10))

PATH_RIGHT_ARROW = 'bitp/assets/right_arrow.png'
IMG_RIGHT_ARROW = pygame.image.load(PATH_RIGHT_ARROW).convert_alpha()
IMG_RIGHT_ARROW = pygame.transform.scale(IMG_RIGHT_ARROW, (10,10))

PATH_RESET = 'bitp/assets/reset.png'
IMG_RESET = pygame.image.load(PATH_RESET).convert_alpha()
IMG_RESET = pygame.transform.scale(IMG_RESET, (80,30))

PATH_RESTART = 'bitp/assets/restart.png'
IMG_RESTART = pygame.image.load(PATH_RESTART).convert_alpha()
IMG_RESTART = pygame.transform.scale(IMG_RESTART, (80,30))

PATH_GRASS = 'bitp/assets/grass.png'
IMG_GRASS = pygame.image.load(PATH_GRASS).convert_alpha()
IMG_GRASS = pygame.transform.scale(IMG_GRASS, (WIDTH,HEIGHT))

swarm = pygame.sprite.Group()
bully_group = pygame.sprite.Group()
menue = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()

class individuum(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.position = pygame.Vector2(np.random.random()*WIDTH, np.random.random()*HEIGHT)
        self.image = IMG_KID
        self.velocity = pygame.Vector2(random.uniform(-PARAMETERS['Swarm Speed'], PARAMETERS['Swarm Speed']), random.uniform(-PARAMETERS['Swarm Speed'], PARAMETERS['Swarm Speed']))
        self.acceleration = pygame.Vector2(0, 0)
        self.rect = pygame.rect.Rect(self.position[0] - 7, self.position[1] - 7, 15, 15)

    def edges(self):
        if self.position.x > WIDTH - 10:
            self.position.x = WIDTH - 10
        elif self.position.x < 10:
            self.position.x = 10

        if self.position.y > HEIGHT - 10:
            self.position.y = HEIGHT - 10
        elif self.position.y < 10:
            self.position.y = 10

    def apply_force(self, force):
        self.acceleration += force
    
    def update(self):
        self.edges()
        self.velocity += self.acceleration
        if self.velocity.length() > PARAMETERS['Swarm Speed']:
            self.velocity.scale_to_length(PARAMETERS['Swarm Speed'])
        self.position += self.velocity
        self.acceleration *= 0
        self.rect = pygame.rect.Rect(self.position[0] - 7, self.position[1] - 7, 15, 15)

    def align(self, boids):
        steering = pygame.Vector2()
        total = 0
        for boid in boids:
            if self.position.distance_to(boid.position) < PARAMETERS['Swarm Radius']:
                steering += boid.velocity
                total += 1
        if total > 0:
            steering /= total
            steering = steering.normalize() * PARAMETERS['Swarm Speed']
            steering -= self.velocity
            if steering.length() > PARAMETERS['Swarm Force']:
                steering.scale_to_length(PARAMETERS['Swarm Force'])
        return steering

    def cohesion(self, boids):
        steering = pygame.Vector2()
        total = 0
        for boid in boids:
            if self.position.distance_to(boid.position) < PARAMETERS['Swarm Radius']:
                steering += boid.position
                total += 1
        if total > 0:
            steering /= total
            steering -= self.position
            if steering.length() > PARAMETERS['Swarm Speed']:
                steering.scale_to_length(PARAMETERS['Swarm Speed'])
            steering -= self.velocity
            if steering.length() > PARAMETERS['Swarm Force']:
                steering.scale_to_length(PARAMETERS['Swarm Force'])
        return steering

    def separation(self, boids):
        steering = pygame.Vector2()
        total = 0
        for boid in boids:
            distance = self.position.distance_to(boid.position)
            if distance < PARAMETERS['Swarm Radius'] and distance > 0:
                diff = self.position - boid.position
                diff /= distance
                steering += diff
                total += 1
        if total > 0:
            steering /= total
            if steering.length() > PARAMETERS['Swarm Speed']:
                steering.scale_to_length(PARAMETERS['Swarm Speed'])
            steering -= self.velocity
            if steering.length() > PARAMETERS['Swarm Force']:
                steering.scale_to_length(PARAMETERS['Swarm Force'])
        return steering

    def avoid_predator(self, predator):
        steering = pygame.Vector2()
        distance = self.position.distance_to(predator)
        if distance < PARAMETERS['Bully Radius']:
            diff = self.position - predator
            diff /= distance
            steering += diff
            if steering.length() > PARAMETERS['Swarm Speed']:
                steering.scale_to_length(PARAMETERS['Swarm Speed'])
            steering -= self.velocity
            if steering.length() > PARAMETERS['Swarm Force']:
                steering.scale_to_length(PARAMETERS['Swarm Force'])
        return steering

    def flock(self, boids, predator):
        alignment = self.align(boids)
        cohesion = self.cohesion(boids)
        separation = self.separation(boids)
        avoidance = self.avoid_predator(predator)

        # Gewichtung der Regeln
        self.apply_force(alignment * PARAMETERS['Allignment'])
        self.apply_force(cohesion * PARAMETERS['Cohesion'])
        self.apply_force(separation * PARAMETERS['Seperation'])
        self.apply_force(avoidance * PARAMETERS['Avoidance'])
    
    def die(self):
        self.kill()

class bully(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.pos = pygame.Vector2(np.random.random()*WIDTH, np.random.random()*HEIGHT)
        self.image = IMG_BULLY
        self.body_count = 0
    
    def update(self, swarm_list):
        min_dist = WIDTH
        goal = self.pos
        for individual in swarm_list:
            if self.pos.distance_to(individual.position) < min_dist:
                goal = (individual.rect[0] + (individual.rect[2] / 2), individual.rect[1] + (individual.rect[3] / 2))
                min_dist = self.pos.distance_to(individual.position)
        movement = (goal[0] - self.pos[0], goal[1] - self.pos[1])
        if movement[0] < 0:
            x_move = max(movement[0], PARAMETERS['Bully Speed'] * -1)
        else:
            x_move = min(movement[0], PARAMETERS['Bully Speed'])
        if movement[1] < 0:
            y_move = max(movement[1], PARAMETERS['Bully Speed'] * -1)
        else:
            y_move = min(movement[1], PARAMETERS['Bully Speed'])
        movement = pygame.Vector2(x_move, y_move)
        self.pos += movement
        self.rect = pygame.rect.Rect(self.pos[0] - 10, self.pos[1] - 15, 20, 30)
        pygame.draw.circle(screen, COLORS['BLACK'],self.pos,PARAMETERS['Bully Radius'], width=1)
        font = pygame.font.SysFont(None, 14)
        bully_text = font.render(str(self.body_count), True, COLORS['BLACK'])
        screen.blit(bully_text, (self.pos[0], self.pos[1] + 15))
    
    def count_up(self):
        self.body_count += 1
    
    def die(self):
        self.kill()


class menu(pygame.sprite.Sprite):

    def __init__(self, *groups) -> None:
        super().__init__(*groups)
        self.image = pygame.Surface((200, 600), pygame.SRCALPHA)
        self.image.fill((0,0,0, 150))

        self.rect = self.image.get_rect()
        self.top_left_x = WIDTH - 200 - 20
        self.top_left_y = 20
        self.rect.topleft = (self.top_left_x, self.top_left_y)

        self.legend = dict()
        for idx, param in enumerate(PARAMETERS.keys()):
            self.legend[param+'left_arrow'] = (self.top_left_x + 70, 
                                               self.top_left_y + 75 + idx * 50,
                                               10,
                                               10)
            self.legend[param+'right_arrow'] = (self.top_left_x + 120, 
                                               self.top_left_y + 75 + idx * 50,
                                               10,
                                               10)
        self.reset_rect = pygame.rect.Rect(self.top_left_x + 15,
                                           self.top_left_y + 560,
                                           80,
                                           30)
        self.restart_rect = pygame.rect.Rect(self.top_left_x + 105,
                                           self.top_left_y + 560,
                                           80,
                                           30)
    
    def update(self):
        self.image = pygame.Surface((200, 600), pygame.SRCALPHA)
        self.image.fill((0,0,0, 150))

        font = pygame.font.SysFont(None, 44)
        param_text = font.render(f"Settings", True, COLORS['WHITE'])
        self.image.blit(param_text, (10, 10))

        font = pygame.font.SysFont(None, 24)
        for idx, param in enumerate(PARAMETERS.keys()):   
            param_text = font.render(f"{param}:", True, COLORS['WHITE'])
            self.image.blit(param_text, (10, 50 + idx * 50))  
            param_text = font.render(f"{PARAMETERS[param]}", True, COLORS['WHITE'])
            self.image.blit(param_text, (100 - len(str(PARAMETERS[param])) * 5, 75 + idx * 50))

            self.image.blit(IMG_LEFT_ARROW,(70, 75 + idx * 50))
            self.image.blit(IMG_RIGHT_ARROW,(120, 75 + idx * 50))

        self.image.blit(IMG_RESET, (15, 560))
        self.image.blit(IMG_RESTART, (105, 560))
        
    def die(self):
        self.kill()

swarm_list = []
bully_list = []

def init_population(swarm_list, bully_list):

    for boid in swarm_list:
        boid.die()

    swarm_list = []
    for _ in range(SWARM_SIZE):
        swarm_list.append(individuum([swarm, all_sprites]))

    for bull in bully_list:
        bull.die()

    bully_list = []
    for _ in range(PARAMETERS['Num Bullies']):
        bully_list.append(bully([bully_group, all_sprites]))

    return swarm_list, bully_list

swarm_list, bully_list = init_population(swarm_list, bully_list)

menu_overlay = menu([all_sprites, menue])

running = True
async def main():
    global running, swarm_list, bully_list, menu_overlay, PARAMETERS, all_sprites, bully_group, menue, swarm, IMG_GRASS, IMG_KID
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type ==pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed(3)[0]:
                    click_pos = pygame.mouse.get_pos()
                    for idx, arrow in enumerate(menu_overlay.legend.values()):
                        if pygame.rect.Rect(arrow).collidepoint(click_pos):
                            change_up = False if idx % 2 == 0 else True
                            flock_param = False if idx < 10 else True
                            PARAMETERS[list(PARAMETERS.keys())[idx // 2]] += ((1 - change_up) * (-1) + change_up) * (1 - (0.9 * flock_param))
                            if flock_param:
                                PARAMETERS[list(PARAMETERS.keys())[idx // 2]] = max(round(PARAMETERS[list(PARAMETERS.keys())[idx // 2]],1),0.0)
                            else:
                                PARAMETERS[list(PARAMETERS.keys())[idx // 2]] = max(int(PARAMETERS[list(PARAMETERS.keys())[idx // 2]]),1)
                    if menu_overlay.reset_rect.collidepoint(click_pos):
                        PARAMETERS = init_params()
                    if menu_overlay.restart_rect.collidepoint(click_pos):
                        PARAMETERS = init_params()
                        swarm_list, bully_list = init_population(swarm_list, bully_list)
                        menu_overlay.die()
                        menu_overlay = menu([all_sprites, menue])
        
        if len(bully_list) < PARAMETERS['Num Bullies']:
            bully_list.append(bully([bully_group, all_sprites]))
        elif len(bully_list) > PARAMETERS['Num Bullies']:
            bully_list[0].die()
            bully_list.pop(0)
            
        screen.fill(COLORS['WHITE'])
        screen.blit(IMG_GRASS,(0,0))

        bully_group.update(swarm_list)

        new_swarm_list = []
        
        for boid in swarm_list:
            save = True
            min_dist_bull = np.random.choice(list(range(len(bully_list))))
            for idx, bull in enumerate(bully_list):
                if boid.position.distance_to(bull.pos) < boid.position.distance_to(bully_list[min_dist_bull].pos):
                    min_dist_bull = idx
                if boid.position.distance_to(bull.pos) <= 10:
                    save = False
                    bull.count_up()
            if save:
                new_swarm_list.append(boid)
                boid.flock(swarm_list, bully_list[min_dist_bull].pos)
            else:
                boid.die()
        swarm_list = new_swarm_list
        
        swarm.update()
        menu_overlay.update()

        swarm.draw(screen)
        bully_group.draw(screen)
        menue.draw(screen)
        
        font = pygame.font.SysFont(None, 24)
        boid_count_text = font.render(f"Boids: {len(swarm_list)}", True, COLORS['BLACK'])
        screen.blit(boid_count_text, (10, 10))

        pygame.display.update()

        await asyncio.sleep(0)  # Let other tasks run
    
    #pygame.quit()

asyncio.run(main())
