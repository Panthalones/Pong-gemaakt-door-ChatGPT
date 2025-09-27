import pygame
import sys
import random

# -------- Settings --------
WIDTH, HEIGHT = 900, 600
FPS = 60

PADDLE_W, PADDLE_H = 12, 110
PADDLE_SPEED = 8

BALL_SIZE = 14
BALL_SPEED_MIN, BALL_SPEED_MAX = 6, 8  # random start speed
BALL_SPEED_INCREASE = 0.35             # little speed-up on every paddle hit
BALL_MAX_SPEED = 16

WIN_SCORE = 10

BG_COLOR = (18, 18, 18)
FG_COLOR = (235, 235, 235)
MIDLINE_COLOR = (90, 90, 90)

# -------- Helpers --------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def random_ball_velocity():
    # Start naar links of rechts, en met willekeurige verticale component
    speed = random.uniform(BALL_SPEED_MIN, BALL_SPEED_MAX)
    angle = random.uniform(-0.6, 0.6)  # ~±34°
    vx = speed * (1 if random.choice([True, False]) else -1)
    vy = speed * angle
    return [vx, vy]

# -------- Game objects --------
class Paddle(pygame.Rect):
    def __init__(self, x):
        super().__init__(x, HEIGHT//2 - PADDLE_H//2, PADDLE_W, PADDLE_H)
        self.dy = 0

    def update(self):
        self.y += self.dy
        self.y = clamp(self.y, 0, HEIGHT - self.height)

class Ball(pygame.Rect):
    def __init__(self):
        super().__init__(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)
        self.vel = random_ball_velocity()
        self.in_play = False  # wacht op spatie om te serveren

    def reset(self, scorer=None):
        self.center = (WIDTH//2, HEIGHT//2)
        self.vel = random_ball_velocity()
        self.in_play = False

    def update(self):
        if not self.in_play:
            return
        self.x += self.vel[0]
        self.y += self.vel[1]

        # Botsing met boven/onder
        if self.top <= 0 and self.vel[1] < 0:
            self.top = 0
            self.vel[1] *= -1
        elif self.bottom >= HEIGHT and self.vel[1] > 0:
            self.bottom = HEIGHT
            self.vel[1] *= -1

# -------- Main --------
def main():
    pygame.init()
    pygame.display.set_caption("Pong")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 48, bold=True)
    small = pygame.font.SysFont("arial", 22)

    left = Paddle(40)
    right = Paddle(WIDTH - 40 - PADDLE_W)
    ball = Ball()

    score_l = 0
    score_r = 0

    running = True
    while running:
        dt = clock.tick(FPS)

        # ---- Input ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_w: left.dy = -PADDLE_SPEED
                if event.key == pygame.K_s: left.dy =  PADDLE_SPEED
                if event.key == pygame.K_UP:   right.dy = -PADDLE_SPEED
                if event.key == pygame.K_DOWN: right.dy =  PADDLE_SPEED
                if event.key == pygame.K_SPACE and not ball.in_play and score_l < WIN_SCORE and score_r < WIN_SCORE:
                    ball.in_play = True
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_s): left.dy = 0
                if event.key in (pygame.K_UP, pygame.K_DOWN): right.dy = 0

        # ---- Update ----
        left.update()
        right.update()

        prev_pos = ball.copy()
        ball.update()

        # Check score (bal uit links/rechts)
        if ball.left <= 0:
            score_r += 1
            ball.reset(scorer="R")
        elif ball.right >= WIDTH:
            score_l += 1
            ball.reset(scorer="L")

        # Paddle collisions (conservatief: alleen wanneer we vanuit buitenzijde binnenkomen)
        if ball.in_play:
            # Links
            if ball.colliderect(left) and prev_pos.left >= left.right - BALL_SIZE:
                ball.left = left.right
                ball.vel[0] = abs(ball.vel[0]) + BALL_SPEED_INCREASE
                ball.vel[0] = min(ball.vel[0], BALL_MAX_SPEED)
                # effect van raakpunt op verticale snelheid
                offset = (ball.centery - left.centery) / (PADDLE_H / 2)
                ball.vel[1] += offset * 2.5

            # Rechts
            if ball.colliderect(right) and prev_pos.right <= right.left + BALL_SIZE:
                ball.right = right.left
                ball.vel[0] = -abs(ball.vel[0]) - BALL_SPEED_INCREASE
                ball.vel[0] = max(ball.vel[0], -BALL_MAX_SPEED)
                offset = (ball.centery - right.centery) / (PADDLE_H / 2)
                ball.vel[1] += offset * 2.5

        # Win check
        game_over = score_l >= WIN_SCORE or score_r >= WIN_SCORE

        # ---- Draw ----
        screen.fill(BG_COLOR)

        # middenstreep
        for y in range(0, HEIGHT, 24):
            pygame.draw.rect(screen, MIDLINE_COLOR, (WIDTH//2 - 2, y, 4, 16))

        # paddles & bal
        pygame.draw.rect(screen, FG_COLOR, left)
        pygame.draw.rect(screen, FG_COLOR, right)
        pygame.draw.ellipse(screen, FG_COLOR, ball)

        # score
        score_txt = font.render(f"{score_l}    {score_r}", True, FG_COLOR)
        rect = score_txt.get_rect(center=(WIDTH//2, 60))
        screen.blit(score_txt, rect)

        # hint
        if not ball.in_play and not game_over:
            hint = small.render("Druk op spatie om te serveren", True, (180, 180, 180))
            screen.blit(hint, hint.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))

        # game over
        if game_over:
            winner = "Links" if score_l > score_r else "Rechts"
            over = font.render(f"{winner} wint!", True, FG_COLOR)
            screen.blit(over, over.get_rect(center=(WIDTH//2, HEIGHT//2 - 10)))
            sub = small.render("Druk op Esc om te sluiten of Spatie om opnieuw te starten", True, (180, 180, 180))
            screen.blit(sub, sub.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))
            # opnieuw starten met spatie
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                score_l = score_r = 0
                left.y = HEIGHT//2 - PADDLE_H//2
                right.y = HEIGHT//2 - PADDLE_H//2
                ball.reset()
                game_over = False

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
