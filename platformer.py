import pygame
import sys
import time
import random

pygame.init()

# Screen setup
is_fullscreen = True
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
font = pygame.font.SysFont("Consolas", 36, bold=True)
big_font = pygame.font.SysFont("Consolas", 80, bold=True)

# Cyberpunk Palette
BG_COLOR = (10, 10, 20)
GRID_COLOR = (20, 20, 40)
PLATFORM_COLOR = (40, 40, 60)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
WHITE = (255, 255, 255)

GRAVITY, JUMP_HEIGHT, SPEED = 0.8, -18, 7 
BULLET_SPEED, RELOAD_TIME, BULLET_DAMAGE = 18, 0.15, 20
WIN_LIMIT = 5

score_p1, score_p2, shake_timer = 0, 0, 0
particles = []

def draw_glow_rect(surface, color, rect, thickness=5):
    for i in range(thickness):
        glow_rect = rect.inflate(i*2, i*2)
        alpha = max(0, 100 - (i * (100//thickness)))
        s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, glow_rect.width, glow_rect.height), border_radius=3)
        surface.blit(s, glow_rect.topleft)

class Particle:
    def __init__(self, x, y, color, velocity):
        self.x, self.y = x, y
        self.color = color
        self.vx, self.vy = velocity
        self.life = 255
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 15
    def draw(self):
        if self.life > 0:
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, self.life), (2, 2), 2)
            screen.blit(s, (self.x, self.y))

class Bullet:
    def __init__(self, x, y, direction, color):
        self.rect = pygame.Rect(x, y, 20, 4)
        self.direction, self.color = direction, color
    def update(self): self.rect.x += self.direction * BULLET_SPEED
    def draw(self, offset):
        r = self.rect.move(offset)
        draw_glow_rect(screen, self.color, r, 4)
        pygame.draw.rect(screen, WHITE, r)

class MovingPlatform:
    def __init__(self, x, y, width, height, distance, speed, start_dir=1):
        self.rect = pygame.Rect(x, y, width, height)
        self.start_x, self.distance, self.speed, self.direction = x, distance, speed, start_dir
    def update(self):
        self.rect.x += self.speed * self.direction
        if abs(self.rect.x - self.start_x) > self.distance: self.direction *= -1
    def draw(self, offset):
        r = self.rect.move(offset)
        pygame.draw.rect(screen, PLATFORM_COLOR, r, border_radius=5)
        pygame.draw.rect(screen, CYAN, r, 2, border_radius=5)

class Player:
    def __init__(self, x, y, color, controls):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.color, self.controls = color, controls # [Left, Right, Jump, Shoot]
        self.reset(x, y)
    
    def reset(self, x, y):
        self.rect.topleft = (x, y)
        self.vel_y = 0
        self.hp = 100
        self.on_ground = False
        self.direction = 1 if x < screen.get_width()/2 else -1
        self.last_shot_time = 0

    def move(self, static, moving):
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[self.controls[0]]: dx -= SPEED; self.direction = -1
        if keys[self.controls[1]]: dx += SPEED; self.direction = 1
        if keys[self.controls[2]] and self.on_ground: self.vel_y = JUMP_HEIGHT; self.on_ground = False
        
        self.vel_y += GRAVITY
        dy = self.vel_y
        
        W = screen.get_width()
        if self.rect.left + dx < 0: dx = -self.rect.left
        if self.rect.right + dx > W: dx = W - self.rect.right

        all_plats = static + [mp.rect for mp in moving]
        self.rect.x += dx
        for p in all_plats:
            if self.rect.colliderect(p):
                if dx > 0: self.rect.right = p.left
                if dx < 0: self.rect.left = p.right
        
        self.on_ground = False
        self.rect.y += dy
        for p in all_plats:
            if self.rect.colliderect(p):
                if dy > 0:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
                elif dy < 0:
                    self.rect.top = p.bottom
                    self.vel_y = 0

    def can_shoot(self):
        return time.time() - self.last_shot_time > RELOAD_TIME

    def shoot(self):
        self.last_shot_time = time.time()
        bx = self.rect.right if self.direction == 1 else self.rect.left - 20
        for _ in range(5):
            particles.append(Particle(bx, self.rect.centery, self.color, (random.uniform(-2, 2), random.uniform(-2, 2))))
        return Bullet(bx, self.rect.centery - 2, self.direction, self.color)

    def draw(self, offset):
        r = self.rect.move(offset)
        draw_glow_rect(screen, self.color, r, 6)
        pygame.draw.rect(screen, self.color, r, border_radius=3)
        gx = r.right if self.direction == 1 else r.left - 25
        pygame.draw.rect(screen, WHITE, (gx, r.centery - 4, 25, 8), border_radius=2)
        pygame.draw.rect(screen, (50, 50, 50), (r.x, r.y - 15, 40, 6))
        pygame.draw.rect(screen, self.color, (r.x, r.y - 15, 40 * (max(0, self.hp)/100), 6))

def setup_map():
    W, H = screen.get_size()
    pw, ph = 160, 20
    static = [
        pygame.Rect(0, H - 40, W, 40),
        pygame.Rect(W*0.05, H-160, pw, ph), pygame.Rect(W*0.95 - pw, H-160, pw, ph),
        pygame.Rect(W//2 - pw//2, H-280, pw, ph),
        pygame.Rect(W*0.05, H-450, pw, ph), pygame.Rect(W*0.95 - pw, H-450, pw, ph),
        pygame.Rect(W//2 - pw//2, H-600, pw, ph)
    ]
    moving = [
        MovingPlatform(W*0.2, H-220, pw, ph, 150, 3, 1),
        MovingPlatform(W*0.8 - pw, H-220, pw, ph, 150, 3, -1),
        MovingPlatform(W*0.3, H-520, pw, ph, 120, 4, -1),
        MovingPlatform(W*0.7 - pw, H-520, pw, ph, 120, 4, 1)
    ]
    return static, moving

static_platforms, moving_platforms = setup_map()
p1 = Player(WIDTH - 150, HEIGHT - 120, CYAN, [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_RSHIFT])
p2 = Player(150, HEIGHT - 120, MAGENTA, [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_SPACE])

bullets, clock = [], pygame.time.Clock()
round_over = match_over = False
winner_msg = ""

while True:
    screen.fill(BG_COLOR)
    W, H = screen.get_size()
    for x in range(0, W, 50): pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, H))
    for y in range(0, H, 50): pygame.draw.line(screen, GRID_COLOR, (0, y), (W, y))

    offset = (random.randint(-8, 8), random.randint(-8, 8)) if shake_timer > 0 else (0, 0)
    if shake_timer > 0: shake_timer -= 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            if event.key == pygame.K_f:
                is_fullscreen = not is_fullscreen
                screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN) if is_fullscreen else pygame.display.set_mode((1280, 720))
                static_platforms, moving_platforms = setup_map()
                p1.reset(screen.get_width()-150, screen.get_height()-120)
                p2.reset(150, screen.get_height()-120)
            
            if not round_over and not match_over:
                if event.key == p1.controls[3] and p1.can_shoot(): bullets.append(p1.shoot())
                if event.key == p2.controls[3] and p2.can_shoot(): bullets.append(p2.shoot())
            elif event.key == pygame.K_r:
                if match_over: score_p1 = score_p2 = 0
                p1.reset(W-150, H-120); p2.reset(150, H-120); bullets = []; round_over = match_over = False

    if not round_over and not match_over:
        for mp in moving_platforms: mp.update()
        p1.move(static_platforms, moving_platforms); p2.move(static_platforms, moving_platforms)
        for b in bullets[:]:
            b.update()
            target = None
            if b.rect.colliderect(p1.rect) and b.color == MAGENTA: target = p1
            elif b.rect.colliderect(p2.rect) and b.color == CYAN: target = p2
            
            if target:
                target.hp -= BULLET_DAMAGE; bullets.remove(b); shake_timer = 12
                for _ in range(15): particles.append(Particle(b.rect.x, b.rect.y, WHITE, (random.uniform(-5, 5), random.uniform(-5, 5))))
            elif b.rect.x < 0 or b.rect.x > W: bullets.remove(b)

        if p1.hp <= 0 or p2.hp <= 0:
            if p1.hp <= 0: score_p2 += 1
            else: score_p1 += 1
            if score_p1 >= WIN_LIMIT or score_p2 >= WIN_LIMIT:
                match_over = True
                winner_msg = "CYAN CHAMPION" if score_p1 >= WIN_LIMIT else "MAGENTA CHAMPION"
            else:
                round_over = True
                winner_msg = "ROUND WON BY " + ("CYAN" if p2.hp <= 0 else "MAGENTA")

    for p in particles[:]:
        p.update(); p.draw()
        if p.life <= 0: particles.remove(p)

    for p in static_platforms: pygame.draw.rect(screen, PLATFORM_COLOR, p.move(offset), border_radius=5)
    for mp in moving_platforms: mp.draw(offset)
    for b in bullets: b.draw(offset)
    p1.draw(offset); p2.draw(offset)
    
    s1 = font.render(f"CYAN: {score_p1}", True, CYAN); screen.blit(s1, (W - 200, 30))
    s2 = font.render(f"MAGENTA: {score_p2}", True, MAGENTA); screen.blit(s2, (50, 30))
    
    if round_over or match_over:
        txt = big_font.render(winner_msg, True, WHITE)
        screen.blit(txt, (W//2 - txt.get_width()//2, H//3))

    pygame.display.flip()
    clock.tick(60)
