import pygame
import math
import random

# Init
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Top-Down Shooter: Waves & GameOver")
clock = pygame.time.Clock()
font_ui = pygame.font.SysFont("Arial", 24, bold=True)
font_big = pygame.font.SysFont("Arial", 64, bold=True)

# --- Assets ---
def get_sprite(color, size, is_player=False):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (0, 0, size, size))
    if is_player:
        pygame.draw.rect(surf, (255, 255, 255), (size//2 - 2, 0, 4, 10))
    return surf

player_img = get_sprite((0, 200, 0), 40, True)
enemy_img = get_sprite((200, 0, 0), 30)
bullet_img = pygame.Surface((10, 10)); bullet_img.fill((255, 255, 0))

class Player:
    def __init__(self):
        self.pos = pygame.Vector2(0, 0)
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        self.kills = 0

    def update(self):
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w]: move.y -= 1
        if keys[pygame.K_s]: move.y += 1
        if keys[pygame.K_a]: move.x -= 1
        if keys[pygame.K_d]: move.x += 1
        if move.length() > 0:
            self.pos += move.normalize() * self.speed

class Bullet:
    def __init__(self, pos, target_world):
        self.pos = pygame.Vector2(pos)
        direction = pygame.Vector2(target_world) - pos
        self.vel = direction.normalize() * 12

    def update(self):
        self.pos += self.vel

class Enemy:
    def __init__(self, player_pos, speed):
        angle = random.uniform(0, math.pi * 2)
        self.pos = player_pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * 600
        self.speed = speed

    def update(self, player_pos):
        dir = (player_pos - self.pos).normalize()
        self.pos += dir * self.speed

def spawn_wave(w, p_pos):
    count = 5 + (w * 2)
    speed = 2 + (w * 0.3)
    return [Enemy(p_pos, speed) for _ in range(count)]

# Reset Game Function
def reset_game():
    p = Player()
    return p, [], spawn_wave(1, p.pos), 1

player, bullets, enemies, wave = reset_game()
game_over = False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            camera_offset = pygame.Vector2(WIDTH // 2, HEIGHT // 2) - player.pos
            mouse_world = pygame.mouse.get_pos() - camera_offset
            bullets.append(Bullet(player.pos, mouse_world))
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                player, bullets, enemies, wave = reset_game()
                game_over = False

    if not game_over:
        # --- Logic ---
        player.update()
        
        if player.kills >= wave * 10:
            wave += 1
            enemies.extend(spawn_wave(wave, player.pos))

        for b in bullets[:]:
            b.update()
            if (b.pos - player.pos).length() > 1000: bullets.remove(b)

        for e in enemies[:]:
            e.update(player.pos)
            for b in bullets[:]:
                if (e.pos - b.pos).length() < 25:
                    if e in enemies: enemies.remove(e)
                    if b in bullets: bullets.remove(b)
                    player.kills += 1
                    if len(enemies) < 5 + (wave * 2):
                        enemies.append(Enemy(player.pos, 2 + (wave * 0.3)))

            if (e.pos - player.pos).length() < 35:
                player.hp -= 0.5
                if player.hp <= 0:
                    game_over = True

    # --- Rendering ---
    camera_offset = pygame.Vector2(WIDTH // 2, HEIGHT // 2) - player.pos
    screen.fill((25, 25, 30))

    # Grid
    grid_size = 80
    off_x, off_y = camera_offset.x % grid_size, camera_offset.y % grid_size
    for x in range(-grid_size, WIDTH + grid_size, grid_size):
        pygame.draw.line(screen, (45, 45, 50), (x + off_x, 0), (x + off_x, HEIGHT))
    for y in range(-grid_size, HEIGHT + grid_size, grid_size):
        pygame.draw.line(screen, (45, 45, 50), (0, y + off_y), (WIDTH, y + off_y))

    # World Objects
    for b in bullets: screen.blit(bullet_img, b.pos + camera_offset - pygame.Vector2(5, 5))
    for e in enemies: screen.blit(enemy_img, e.pos + camera_offset - pygame.Vector2(15, 15))

    # Player
    mx, my = pygame.mouse.get_pos()
    rel_x, rel_y = mx - (WIDTH // 2), my - (HEIGHT // 2)
    angle = math.degrees(math.atan2(-rel_y, rel_x)) - 90
    rotated_player = pygame.transform.rotate(player_img, angle)
    screen.blit(rotated_player, rotated_player.get_rect(center=(WIDTH//2, HEIGHT//2)).topleft)

    # UI
    pygame.draw.rect(screen, (200, 0, 0), (20, 20, 200, 20))
    pygame.draw.rect(screen, (0, 200, 0), (20, 20, max(0, player.hp * 2), 20))
    screen.blit(font_ui.render(f"WAVE: {wave}  KILLS: {player.kills}", True, (255, 255, 255)), (20, 50))

    # Game Over Overlay
    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Semi-transparent black
        screen.blit(overlay, (0,0))
        
        go_text = font_big.render("GAME OVER", True, (255, 50, 50))
        score_text = font_ui.render(f"Final Score: {player.kills} kills in Wave {wave}", True, (255, 255, 255))
        retry_text = font_ui.render("Press 'R' to Restart", True, (200, 200, 200))
        
        screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 80))
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
        screen.blit(retry_text, (WIDTH//2 - retry_text.get_width()//2, HEIGHT//2 + 50))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
