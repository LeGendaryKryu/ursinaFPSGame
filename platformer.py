import pygame
import sys
import time
import random

pygame.init()

# Initial Screen setup
is_fullscreen = True
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
font = pygame.font.SysFont("Arial", 36)
big_font = pygame.font.SysFont("Arial", 80)

# Colors & Constants
WHITE, RED, BLUE, GREEN, BLACK, DARK_GRAY = (255,255,255), (255,0,0), (0,0,255), (0,255,0), (0,0,0), (50,50,50)
GRAVITY, JUMP_HEIGHT, SPEED = 0.8, -18, 7 
BULLET_SPEED, RELOAD_TIME, BULLET_DAMAGE = 15, 0.2, 20
WIN_LIMIT = 5

score_p1 = 0 
score_p2 = 0 
shake_timer = 0

class Bullet:
    def __init__(self, x, y, direction, color):
        self.rect = pygame.Rect(x, y, 15, 5)
        self.direction = direction
        self.color = color
    def update(self): self.rect.x += self.direction * BULLET_SPEED
    def draw(self, offset): 
        pygame.draw.rect(screen, self.color, self.rect.move(offset))

class MovingPlatform:
    def __init__(self, x, y, width, height, distance, speed, start_dir=1):
        self.rect = pygame.Rect(x, y, width, height)
        self.start_x = x
        self.distance = distance
        self.speed = speed
        self.direction = start_dir
    def update(self):
        self.rect.x += self.speed * self.direction
        if abs(self.rect.x - self.start_x) > self.distance:
            self.direction *= -1
    def draw(self, offset):
        pygame.draw.rect(screen, BLACK, self.rect.move(offset))

class Player:
    def __init__(self, x, y, color, controls):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.color = color
        self.controls = controls # [Left, Right, Jump, Shoot]
        self.hp = 100
        self.vel_y = 0
        self.on_ground = False
        self.direction = 1
        self.last_shot_time = 0

    def reset(self, x, y):
        self.rect.topleft = (x, y)
        self.vel_y = 0
        self.hp = 100
        self.direction = 1 if x < screen.get_width()/2 else -1

    def move(self, static_platforms, moving_platforms):
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

        all_plats = static_platforms + [mp.rect for mp in moving_platforms]
        
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

    def can_shoot(self): return time.time() - self.last_shot_time > RELOAD_TIME
    def shoot(self):
        self.last_shot_time = time.time()
        bx = self.rect.right if self.direction == 1 else self.rect.left - 15
        return Bullet(bx, self.rect.centery - 2, self.direction, self.color)
    def draw(self, offset):
        r = self.rect.move(offset)
        pygame.draw.rect(screen, self.color, r)
        gx = r.right if self.direction == 1 else r.left - 25
        pygame.draw.rect(screen, DARK_GRAY, (gx, r.centery - 5, 25, 10))
        pygame.draw.rect(screen, RED, (r.x, r.y - 15, 40, 5))
        pygame.draw.rect(screen, GREEN, (r.x, r.y - 15, 40 * (max(0, self.hp)/100), 5))

def setup_map():
    W, H = screen.get_size()
    pw, ph = 160, 20
    static = [
        pygame.Rect(0, H - 40, W, 40), # Пол
        
        # Ярус 1: Статичные по бокам
        pygame.Rect(W*0.05, H-160, pw, ph), 
        pygame.Rect(W*0.95 - pw, H-160, pw, ph),
        
        # Ярус 2: Одна центральная
        pygame.Rect(W//2 - pw//2, H-280, pw, ph),
        
        # Ярус 4: Статичные по бокам (выше)
        pygame.Rect(W*0.05, H-450, pw, ph), 
        pygame.Rect(W*0.95 - pw, H-450, pw, ph),
        
        # Ярус 5: Пик в центре
        pygame.Rect(W//2 - pw//2, H-600, pw, ph)
    ]
    
    # Движущиеся платформы теперь строго симметричны
    moving = [
        # Пара на Ярусе 1.5 (движутся навстречу друг другу и обратно)
        MovingPlatform(W*0.2, H-220, pw, ph, 150, 3, 1),
        MovingPlatform(W*0.8 - pw, H-220, pw, ph, 150, 3, -1),
        
        # Пара на Ярусе 3.5 (движутся от центра к краям и обратно)
        MovingPlatform(W*0.3, H-520, pw, ph, 120, 4, -1),
        MovingPlatform(W*0.7 - pw, H-520, pw, ph, 120, 4, 1)
    ]
    return static, moving



static_platforms, moving_platforms = setup_map()
# P1: Blue (Right side), P2: Red (Left side)
p1 = Player(WIDTH - 150, HEIGHT - 120, BLUE, [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_RSHIFT])
p2 = Player(150, HEIGHT - 120, RED, [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_SPACE])

bullets = []
clock = pygame.time.Clock()
round_over = match_over = False
winner_msg = ""

while True:
    screen.fill(WHITE)
    W, H = screen.get_size()
    offset = (random.randint(-8, 8), random.randint(-8, 8)) if shake_timer > 0 else (0, 0)
    if shake_timer > 0: shake_timer -= 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            
            if event.key == pygame.K_f: # Toggle Fullscreen
                is_fullscreen = not is_fullscreen
                screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN) if is_fullscreen else pygame.display.set_mode((1280, 720))
                static_platforms, moving_platforms = setup_map()
                p1.reset(screen.get_width() - 150, screen.get_height() - 120)
                p2.reset(150, screen.get_height() - 120)

            if not round_over and not match_over:
                if event.key == p1.controls[3] and p1.can_shoot(): bullets.append(p1.shoot())
                if event.key == p2.controls[3] and p2.can_shoot(): bullets.append(p2.shoot())
            elif event.key == pygame.K_r:
                if match_over: score_p1 = score_p2 = 0
                p1.reset(W - 150, H - 120); p2.reset(150, H - 120)
                bullets = []; round_over = match_over = False

    if not round_over and not match_over:
        for mp in moving_platforms: mp.update()
        p1.move(static_platforms, moving_platforms); p2.move(static_platforms, moving_platforms)
        for b in bullets[:]:
            b.update()
            if b.rect.colliderect(p1.rect) and b.color == RED:
                p1.hp -= BULLET_DAMAGE; bullets.remove(b); shake_timer = 12
            elif b.rect.colliderect(p2.rect) and b.color == BLUE:
                p2.hp -= BULLET_DAMAGE; bullets.remove(b); shake_timer = 12
            elif b.rect.x < 0 or b.rect.x > W: bullets.remove(b)

        if p1.hp <= 0 or p2.hp <= 0:
            if p1.hp <= 0: score_p2 += 1
            else: score_p1 += 1
            if score_p1 >= WIN_LIMIT or score_p2 >= WIN_LIMIT:
                match_over = True
                winner_msg = "CHAMPION: BLUE" if score_p1 >= WIN_LIMIT else "CHAMPION: RED"
            else:
                round_over = True
                winner_msg = "ROUND WON BY " + ("BLUE" if p2.hp <= 0 else "RED")

    for p in static_platforms: pygame.draw.rect(screen, BLACK, p.move(offset))
    for mp in moving_platforms: mp.draw(offset)
    for b in bullets: b.draw(offset)
    p1.draw(offset); p2.draw(offset)
    
    s1 = font.render(f"Blue: {score_p1}", True, BLUE)
    s2 = font.render(f"Red: {score_p2}", True, RED)
    screen.blit(s1, (W - 150, 20)); screen.blit(s2, (50, 20))
    
    if round_over or match_over:
        txt = big_font.render(winner_msg, True, GREEN if match_over else BLACK)
        sub_txt = font.render("Press 'R' to Continue", True, BLACK)
        screen.blit(txt, (W//2 - txt.get_width()//2, H//3))
        screen.blit(sub_txt, (W//2 - sub_txt.get_width()//2, H//2))

    pygame.display.flip()
    clock.tick(60)
