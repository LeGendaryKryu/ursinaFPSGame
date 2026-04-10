import pygame
import math
import random
import time

# Init
pygame.init()
info = pygame.display.Info()
MONITOR_W, MONITOR_H = info.current_w, info.current_h
WIDTH, HEIGHT = MONITOR_W, MONITOR_H

# Initial display setup
is_fullscreen = True
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Top-Down Shooter")
clock = pygame.time.Clock()

# Fonts
font_ui = pygame.font.SysFont("Arial", 24, bold=True)
font_big = pygame.font.SysFont("Arial", 64, bold=True)

# --- Assets ---
def get_player_with_gun():
    surf = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.rect(surf, (0, 200, 100), (5, 5, 40, 40)) 
    pygame.draw.rect(surf, (150, 150, 150), (35, 10, 10, 25)) 
    return surf

player_base_img = get_player_with_gun()
enemy_img = pygame.Surface((35, 35), pygame.SRCALPHA)
pygame.draw.rect(enemy_img, (220, 50, 50), (0, 0, 35, 35))
bullet_img = pygame.Surface((12, 6)); bullet_img.fill((255, 215, 0))

class Player:
    def __init__(self):
        self.pos = pygame.Vector2(0, 0)
        self.speed = 6
        self.hp = 100
        self.kills = 0
        self.ammo_max = 30
        self.ammo_current = 30
        self.is_reloading = False
        self.reload_start_time = 0
        self.reload_duration = 1.5
        self.last_shot_time = 0
        self.fire_delay = 0.12 
        self.current_spread = 0
        self.max_spread = 15
        self.spread_inc = 1.5

    def update(self):
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w]: move.y -= 1
        if keys[pygame.K_s]: move.y += 1
        if keys[pygame.K_a]: move.x -= 1
        if keys[pygame.K_d]: move.x += 1
        if move.length() > 0:
            self.pos += move.normalize() * self.speed
        if keys[pygame.K_r] and not self.is_reloading and self.ammo_current < self.ammo_max:
            self.start_reload()
        if self.is_reloading:
            if time.time() - self.reload_start_time >= self.reload_duration:
                self.ammo_current = self.ammo_max
                self.is_reloading = False

    def start_reload(self):
        self.is_reloading = True
        self.reload_start_time = time.time()

    def shoot(self, target_world):
        current_time = time.time()
        if not self.is_reloading and current_time - self.last_shot_time >= self.fire_delay:
            if self.ammo_current > 0:
                self.ammo_current -= 1
                self.last_shot_time = current_time
                spread_angle = random.uniform(-self.current_spread, self.current_spread)
                self.current_spread = min(self.max_spread, self.current_spread + self.spread_inc)
                return Bullet(self.pos, target_world, spread_angle)
            else:
                self.start_reload()
        return None

class Bullet:
    def __init__(self, pos, target_world, spread_offset):
        self.pos = pygame.Vector2(pos)
        direction = pygame.Vector2(target_world) - pos
        base_angle = math.atan2(direction.y, direction.x)
        final_angle = base_angle + math.radians(spread_offset)
        self.angle = math.degrees(-final_angle)
        self.vel = pygame.Vector2(math.cos(final_angle), math.sin(final_angle)) * 22

    def update(self):
        self.pos += self.vel

class Enemy:
    def __init__(self, player_pos, speed):
        angle = random.uniform(0, math.pi * 2)
        self.pos = player_pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * (WIDTH // 1.2)
        self.speed = speed

    def update(self, player_pos):
        dir = (player_pos - self.pos).normalize()
        self.pos += dir * self.speed

# Init Game
player = Player()
bullets = []
enemies = [Enemy(player.pos, 2) for _ in range(6)]
wave = 1
game_over = False

# Main Loop
while True:
    screen.fill((20, 20, 25))
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); exit()
        
        if event.type == pygame.KEYDOWN:
            # FULLSCREEN TOGGLE
            if event.key == pygame.K_f:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    WIDTH, HEIGHT = MONITOR_W, MONITOR_H
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                else:
                    WIDTH, HEIGHT = 1280, 720
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
            
            # ESCAPE LOGIC
            if event.key == pygame.K_ESCAPE:
                if is_fullscreen:
                    is_fullscreen = False
                    WIDTH, HEIGHT = 1280, 720
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
                else:
                    pygame.quit(); exit()

            if event.key == pygame.K_r and game_over:
                player = Player(); bullets = []; enemies = [Enemy(player.pos, 2)]; wave = 1; game_over = False

    if not game_over:
        player.update()
        
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if mouse_pressed:
            cam_off = pygame.Vector2(WIDTH//2, HEIGHT//2) - player.pos
            mouse_world = pygame.mouse.get_pos() - cam_off
            b = player.shoot(mouse_world)
            if b: bullets.append(b)
        else:
            player.current_spread = 0

        if player.kills >= wave * 10:
            wave += 1
            for _ in range(2): enemies.append(Enemy(player.pos, 2 + wave * 0.1))

        for b in bullets[:]:
            b.update()
            if (b.pos - player.pos).length() > WIDTH: bullets.remove(b)

        for e in enemies[:]:
            e.update(player.pos)
            for b in bullets[:]:
                if (e.pos - b.pos).length() < 30:
                    if e in enemies: enemies.remove(e)
                    if b in bullets: bullets.remove(b)
                    player.kills += 1
                    enemies.append(Enemy(player.pos, 2 + wave * 0.1))
            if (e.pos - player.pos).length() < 40:
                player.hp -= 0.5
                if player.hp <= 0: game_over = True

    # Render
    cam_off = pygame.Vector2(WIDTH//2, HEIGHT//2) - player.pos
    for b in bullets:
        rot_b = pygame.transform.rotate(bullet_img, b.angle)
        screen.blit(rot_b, b.pos + cam_off)
    for e in enemies: screen.blit(enemy_img, e.pos + cam_off)

    mx, my = pygame.mouse.get_pos()
    angle = math.degrees(math.atan2(-(my - HEIGHT//2), mx - WIDTH//2)) - 90
    rot_p = pygame.transform.rotate(player_base_img, angle)
    screen.blit(rot_p, rot_p.get_rect(center=(WIDTH//2, HEIGHT//2)))

    # UI
    pygame.draw.rect(screen, (100, 0, 0), (20, 20, 200, 15))
    pygame.draw.rect(screen, (0, 255, 100), (20, 20, max(0, player.hp * 2), 15))
    ammo_label = "RELOADING..." if player.is_reloading else f"AMMO: {player.ammo_current}/{player.ammo_max}"
    screen.blit(font_ui.render(ammo_label, True, (255, 255, 255)), (20, 45))
    screen.blit(font_ui.render(f"WAVE: {wave} | KILLS: {player.kills}", True, (255, 255, 255)), (20, 75))
    screen.blit(font_ui.render("'F' Fullscreen | 'ESC' Window/Exit", True, (120, 120, 120)), (20, HEIGHT - 40))

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,220))
        screen.blit(overlay, (0,0))
        msg = font_big.render("YOU DIED", True, (255, 0, 0))
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))
        sub = font_ui.render(f"Final Score: {player.kills} | Press 'R' to Restart", True, (255, 255, 255))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 40))

    pygame.display.flip()
