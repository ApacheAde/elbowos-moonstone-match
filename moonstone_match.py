#!/usr/bin/env python3
"""Moonstone Match — neon match-3 arcade for ElbowOS. Python 3 + pygame."""
import os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/MOONSTONE_MATCH_ElbowOS.mp4")
TITLE, HANDLE = "MOONSTONE MATCH", "x.com/ElbowOS"

NAVY = (8, 6, 22)
PURPLE = (90, 40, 160)
CYAN = (0, 220, 255)
MAGENTA = (255, 50, 180)
GOLD = (255, 210, 60)
LIME = (80, 255, 120)
PINK = (255, 120, 200)
COLORS = [CYAN, MAGENTA, GOLD, LIME, PINK]
GRID_W, GRID_H = 7, 11
CELL = 120
OX, OY = (W - GRID_W * CELL) // 2, 280

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            self.screen = pygame.display.set_mode((W, H))
        self.font_lg = pygame.font.SysFont("arial", 72, bold=True)
        self.font_sm = pygame.font.SysFont("arial", 36)
        self.clock = pygame.time.Clock()
        self.grid = [[random.choice(COLORS) for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.score = 0
        self.combo = 0
        self.sel = None
        self.t = 0
        self.clear_matches()

    def clear_matches(self):
        matched = set()
        for y in range(GRID_H):
            for x in range(GRID_W - 2):
                if self.grid[y][x] == self.grid[y][x+1] == self.grid[y][x+2] and self.grid[y][x]:
                    matched.update([(x, y), (x+1, y), (x+2, y)])
        for x in range(GRID_W):
            for y in range(GRID_H - 2):
                if self.grid[y][x] == self.grid[y+1][x] == self.grid[y+2][x] and self.grid[y][x]:
                    matched.update([(x, y), (x, y+1), (x, y+2)])
        if matched:
            self.score += len(matched) * 10 * (1 + self.combo)
            self.combo += 1
            for x, y in matched:
                self.grid[y][x] = None
            self.drop()
            return True
        self.combo = 0
        return False

    def drop(self):
        for x in range(GRID_W):
            col = [self.grid[y][x] for y in range(GRID_H) if self.grid[y][x]]
            col = [None] * (GRID_H - len(col)) + col
            for y in range(GRID_H):
                self.grid[y][x] = col[y]
        for y in range(GRID_H):
            for x in range(GRID_W):
                if self.grid[y][x] is None:
                    self.grid[y][x] = random.choice(COLORS)
        self.clear_matches()

    def swap(self, a, b):
        ax, ay = a
        bx, by = b
        self.grid[ay][ax], self.grid[by][bx] = self.grid[by][bx], self.grid[ay][ax]
        if not self.clear_matches():
            self.grid[ay][ax], self.grid[by][bx] = self.grid[by][bx], self.grid[ay][ax]

    def find_swap(self):
        dirs = [(1, 0), (0, 1)]
        for y in range(GRID_H):
            for x in range(GRID_W):
                for dx, dy in dirs:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                        self.grid[y][x], self.grid[ny][nx] = self.grid[ny][nx], self.grid[y][x]
                        if self.would_match():
                            self.grid[y][x], self.grid[ny][nx] = self.grid[ny][nx], self.grid[y][x]
                            return (x, y), (nx, ny)
                        self.grid[y][x], self.grid[ny][nx] = self.grid[ny][nx], self.grid[y][x]
        return None

    def would_match(self):
        for y in range(GRID_H):
            for x in range(GRID_W - 2):
                if self.grid[y][x] == self.grid[y][x+1] == self.grid[y][x+2]:
                    return True
        for x in range(GRID_W):
            for y in range(GRID_H - 2):
                if self.grid[y][x] == self.grid[y+1][x] == self.grid[y+2][x]:
                    return True
        return False

    def draw(self, surf):
        surf.fill(NAVY)
        for i in range(20):
            pygame.draw.circle(surf, (20, 10, 50), (random.randint(0, W), random.randint(0, H)), 2)
        title = self.font_lg.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W//2, 120)))
        handle = self.font_sm.render(HANDLE, True, CYAN)
        surf.blit(handle, handle.get_rect(center=(W//2, 200)))
        for y in range(GRID_H):
            for x in range(GRID_W):
                c = self.grid[y][x]
                if c:
                    rect = pygame.Rect(OX + x*CELL + 8, OY + y*CELL + 8, CELL-16, CELL-16)
                    pygame.draw.rect(surf, c, rect, border_radius=20)
                    pygame.draw.rect(surf, (255, 255, 255), rect, 3, border_radius=20)
                    glow = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (*c, 60), (0, 0, CELL, CELL), border_radius=24)
                    surf.blit(glow, (OX + x*CELL, OY + y*CELL))
        sc = self.font_lg.render(f"SCORE {self.score}", True, MAGENTA)
        surf.blit(sc, sc.get_rect(center=(W//2, H - 180)))
        hint = self.font_sm.render("click adjacent gems to swap", True, LIME)
        surf.blit(hint, hint.get_rect(center=(W//2, H - 80)))

    def update(self, auto=False):
        self.t += 1
        if auto and self.t % 12 == 0:
            move = self.find_swap()
            if move:
                self.swap(*move)
            else:
                for _ in range(3):
                    x, y = random.randrange(GRID_W), random.randrange(GRID_H)
                    nx = min(GRID_W-1, x+1)
                    self.grid[y][x], self.grid[y][nx] = self.grid[y][nx], self.grid[y][x]
                self.clear_matches()

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = ev.pos
                    gx, gy = (mx - OX) // CELL, (my - OY) // CELL
                    if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
                        if self.sel is None:
                            self.sel = (gx, gy)
                        else:
                            if abs(gx - self.sel[0]) + abs(gy - self.sel[1]) == 1:
                                self.swap(self.sel, (gx, gy))
                            self.sel = None
            self.update()
            self.draw(self.screen)
            if self.sel:
                x, y = self.sel
                pygame.draw.rect(self.screen, GOLD, (OX + x*CELL, OY + y*CELL, CELL, CELL), 6)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", "20", "-movflags", "+faststart", OUT]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for i in range(frames):
                self.update(auto=True)
                self.draw(self.screen)
                raw = pygame.image.tostring(self.screen, "RGB")
                proc.stdin.write(raw)
                if i % 30 == 0:
                    print(f"frame {i}/{frames} score={self.score}")
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode()
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
