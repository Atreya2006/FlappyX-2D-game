import pygame
from pygame.locals import *
import random
import os

pygame.init()

# ————— Constants & Config —————
FPS = 60
SCREEN_W, SCREEN_H = 864, 936
WHITE = (255,255,255)

# Difficulty settings
DIFFICULTY = {
    1: {'gap': 200, 'speed': 3},
    2: {'gap': 150, 'speed': 4},
    3: {'gap': 120, 'speed': 5}
}
current_diff = 2  # start on Medium

# State variables
clock         = pygame.time.Clock()
screen        = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Flappy Bird")
font_large    = pygame.font.SysFont('Bauhaus 93', 60)
font_med      = pygame.font.SysFont('Arial', 30)

started       = False
flying        = False
game_over     = False
score         = 0
high_score    = 0
pass_pipe     = False
last_pipe_time= 0

def load_img(name):
    return pygame.image.load(os.path.join(name))

# Assets
bg         = load_img('bg.png')
ground_img = load_img('ground.png')
pipe_img   = load_img('pipe.png')
btn_img    = load_img('restart.png')

# Sprite groups
bird_group = pygame.sprite.Group()
pipe_group = pygame.sprite.Group()

class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.frames = [load_img(f'bird{n}.png') for n in range(1,4)]
        self.index = 0
        self.counter = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=(100, SCREEN_H//2))
        self.vel = 0
        self.clicked = False

    def update(self):
        global flying, event_touch

        # Gravity
        if flying:
            self.vel += 0.5
            if self.vel > 10: self.vel = 10
            if self.rect.bottom < SCREEN_H - 168:
                self.rect.y += int(self.vel)

        # Flap on click/tap
        if not game_over and (pygame.mouse.get_pressed()[0] or event_touch) and not self.clicked:
            self.clicked = True
            self.vel = -10
        if not pygame.mouse.get_pressed()[0] and not event_touch:
            self.clicked = False

        # Animate & rotate
        self.counter += 1
        if self.counter > 5:
            self.counter = 0
            self.index = (self.index + 1) % len(self.frames)
        angle = -self.vel*2 if not game_over else -90
        self.image = pygame.transform.rotate(self.frames[self.index], angle)

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, inverted=False):
        super().__init__()
        self.image = pipe_img if not inverted else pygame.transform.flip(pipe_img, False, True)
        if inverted:
            self.rect = self.image.get_rect(midbottom=(x,y))
        else:
            self.rect = self.image.get_rect(midtop=(x,y))

    def update(self):
        speed = DIFFICULTY[current_diff]['speed']
        self.rect.x -= speed
        if self.rect.right < 0:
            self.kill()

class Button:
    def __init__(self, x,y, img):
        self.image = img
        self.rect = img.get_rect(center=(x,y))
    def draw(self):
        screen.blit(self.image, self.rect)
        if pygame.mouse.get_pressed()[0] and self.rect.collidepoint(pygame.mouse.get_pos()):
            return True
        return False

# Instantiate objects
flappy = Bird()
bird_group.add(flappy)
button = Button(SCREEN_W//2, SCREEN_H//2 - 100, btn_img)

def draw_text(text,font,color,x,y):
    img = font.render(text,True,color)
    screen.blit(img,(x,y))

# Main loop
running = True
while running:
    clock.tick(FPS)
    event_touch = False

    for ev in pygame.event.get():
        if ev.type == QUIT or (ev.type==KEYDOWN and ev.key==K_ESCAPE):
            running = False
        if ev.type == KEYDOWN:
            if ev.key in (K_1, K_2, K_3):
                current_diff = int(ev.unicode)
        if ev.type == MOUSEBUTTONDOWN:
            event_touch = True

    # Draw background
    screen.blit(bg, (0,0))

    if not started:
        # Start screen
        draw_text('Flappy Bird', font_large, WHITE, SCREEN_W//2-180, 200)
        draw_text('Click/Tap to Start', font_med, WHITE, SCREEN_W//2-100, 300)
        draw_text('1/2/3:Difficulty', font_med, WHITE, 50, SCREEN_H-140)
        if event_touch:
            started = True
            flying = True
            last_pipe_time = pygame.time.get_ticks()
    else:
        # Spawn pipes
        now = pygame.time.get_ticks()
        if now - last_pipe_time > 1500:
            offset = random.randint(-100,100)
            gap = DIFFICULTY[current_diff]['gap']
            pipe_group.add(Pipe(SCREEN_W, SCREEN_H//2 + offset + gap//2))
            pipe_group.add(Pipe(SCREEN_W, SCREEN_H//2 + offset - gap//2, True))
            last_pipe_time = now

        # Update & draw sprites
        bird_group.draw(screen)
        bird_group.update()
        pipe_group.draw(screen)
        pipe_group.update()

        # Draw ground
        speed = DIFFICULTY[current_diff]['speed']
        ground_x = -(pygame.time.get_ticks() // speed) % ground_img.get_width()
        screen.blit(ground_img, (ground_x, SCREEN_H-168))

        # Score — only while game active
        if not game_over and pipe_group:
            p = pipe_group.sprites()[0]
            if flappy.rect.left > p.rect.left and flappy.rect.right < p.rect.right and not pass_pipe:
                score += 1
                pass_pipe = True
            if pass_pipe and flappy.rect.left > p.rect.right:
                pass_pipe = False

        draw_text(str(score), font_large, WHITE, SCREEN_W//2-20, 50)

        # Collisions
        if pygame.sprite.groupcollide(bird_group, pipe_group, False, False) \
           or flappy.rect.top<0 or flappy.rect.bottom>SCREEN_H-168:
            game_over = True
            flying = False

        # Game Over
        if game_over:
            draw_text('Game Over', font_large, WHITE, SCREEN_W//2-180, 200)
            draw_text(f'Score: {score}  High: {max(score,high_score)}',
                      font_med, WHITE, SCREEN_W//2-200, 300)
            if button.draw():
                high_score = max(high_score, score)
                score = 0
                started = False
                game_over = False
                pipe_group.empty()
                flappy.rect.center = (100, SCREEN_H//2)
                flappy.vel = 0

    pygame.display.update()

pygame.quit()
