import random
import pygame

# ---------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------
CELL_SIZE = 40
ROWS, COLS = 13, 13
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE

# Colores (R, G, B)
BG = (56, 142, 60)        # Suelo
HARD = (97, 97, 97)       # Muro indestructible
SOFT = (216, 67, 21)      # Caja destructible
PLAYER = (33, 150, 243)   # Jugador
BOMB = (33, 33, 33)       # Bomba
FIRE = (255, 235, 59)     # Explosión
EXIT = (0, 229, 255)      # Salida
ENEMY = (233, 30, 99)     # Enemigo
WHITE = (255, 255, 255)

# Celdas
FLOOR, WALL, BOX = 0, 1, 2

START = (1, 1)
GOAL = (ROWS - 2, COLS - 2)
# Zonas que siempre quedan libres (inicio y salida)
SAFE_CELLS = {(1, 1), (1, 2), (2, 1),
              (ROWS - 2, COLS - 2), (ROWS - 2, COLS - 3), (ROWS - 3, COLS - 2)}

# ---------------------------------------------------------------
# Mapa del nivel 2: '#' = muro indestructible, '.' = espacio (puede tener caja)
# ---------------------------------------------------------------
LEVEL_NUMBER = 2

LAYOUT = [
    "#############",
    "#...........#",
    "#.#.#.#.#.#.#",
    "#.....#.....#",
    "#.#.#.#.#.#.#",
    "#...#...#...#",
    "#.#.#.#.#.#.#",
    "#...#...#...#",
    "#.#.#.#.#.#.#",
    "#.....#.....#",
    "#.#.#.#.#.#.#",
    "#...........#",
    "#############",
]

# Dificultad de este nivel
LEVELS = [
    {"layout": LAYOUT, "box_density": 0.65, "fuse": 100, "blast": 2,
     "enemies": 2, "enemy_delay": 32},
]

# ---------------------------------------------------------------
# Inicialización de pygame
# ---------------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomberman - Nivel 2")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 56)

# ---------------------------------------------------------------
# Estado del juego
# ---------------------------------------------------------------
current_level = 0
cfg = LEVELS[0]
grid = []
player_r, player_c = START
bombs = []        # [r, c, timer]
explosions = []   # [r, c, timer]
enemies = []      # [r, c, timer]


def build_grid(level):
    new_grid = []
    for r, line in enumerate(level["layout"]):
        row = []
        for c, ch in enumerate(line):
            if ch == "#":
                row.append(WALL)
            elif (r, c) in SAFE_CELLS:
                row.append(FLOOR)
            else:
                row.append(BOX if random.random() < level["box_density"] else FLOOR)
        new_grid.append(row)
    return new_grid


def spawn_enemies(count, delay):
    # Solo en celdas libres y lejos del jugador
    candidates = [
        (r, c) for r in range(ROWS) for c in range(COLS)
        if grid[r][c] == FLOOR
        and abs(r - START[0]) + abs(c - START[1]) > 6
        and (r, c) != GOAL
    ]
    chosen = random.sample(candidates, min(count, len(candidates)))
    return [[r, c, random.randint(0, delay)] for r, c in chosen]


def load_level(index):
    global current_level, cfg, grid, player_r, player_c
    current_level = index
    cfg = LEVELS[index]
    grid = build_grid(cfg)
    player_r, player_c = START
    bombs.clear()
    explosions.clear()
    enemies.clear()
    enemies.extend(spawn_enemies(cfg["enemies"], cfg["enemy_delay"]))


def show_message(text):
    draw_elements()
    label = big_font.render(text, True, WHITE)
    shadow = big_font.render(text, True, (0, 0, 0))
    x = (WIDTH - label.get_width()) // 2
    y = (HEIGHT - label.get_height()) // 2
    screen.blit(shadow, (x + 2, y + 2))
    screen.blit(label, (x, y))
    pygame.display.flip()
    pygame.time.wait(1200)
    pygame.event.clear()  # descarta teclas pulsadas durante la pausa


def die():
    show_message("¡Moriste!")
    load_level(0)  # reinicia este mismo nivel


def next_level():
    show_message("¡Nivel completado!")
    load_level(0)  # vuelve a empezar este nivel


# ---------------------------------------------------------------
# Lógica
# ---------------------------------------------------------------
def place_bomb():
    if not any(b[0] == player_r and b[1] == player_c for b in bombs):
        bombs.append([player_r, player_c, cfg["fuse"]])


def explode(r, c):
    explosions.append([r, c, 20])
    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        for i in range(1, cfg["blast"] + 1):
            nr, nc = r + dr * i, c + dc * i
            if not (0 <= nr < ROWS and 0 <= nc < COLS) or grid[nr][nc] == WALL:
                break  # el muro detiene la explosión
            explosions.append([nr, nc, 20])
            if grid[nr][nc] == BOX:
                grid[nr][nc] = FLOOR  # destruye la caja y se detiene
                break


def update_bombs():
    for bomb in bombs[:]:
        bomb[2] -= 1
        if bomb[2] <= 0:
            bombs.remove(bomb)
            explode(bomb[0], bomb[1])


def update_explosions():
    for exp in explosions[:]:
        exp[2] -= 1
        if exp[2] <= 0:
            explosions.remove(exp)


def update_enemies():
    bomb_cells = {(b[0], b[1]) for b in bombs}
    enemy_cells = {(e[0], e[1]) for e in enemies}
    for enemy in enemies[:]:
        # Las explosiones matan enemigos
        if any(enemy[0] == er and enemy[1] == ec for er, ec, _ in explosions):
            enemies.remove(enemy)
            continue

        enemy[2] -= 1
        if enemy[2] > 0:
            continue
        enemy[2] = cfg["enemy_delay"]

        options = []
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = enemy[0] + dr, enemy[1] + dc
            if (grid[nr][nc] == FLOOR
                    and (nr, nc) not in bomb_cells
                    and (nr, nc) not in enemy_cells):
                options.append((nr, nc))
        if options:
            enemy_cells.discard((enemy[0], enemy[1]))
            enemy[0], enemy[1] = random.choice(options)
            enemy_cells.add((enemy[0], enemy[1]))


def player_is_dead():
    in_fire = any(er == player_r and ec == player_c for er, ec, _ in explosions)
    hit_enemy = any(er == player_r and ec == player_c for er, ec, _ in enemies)
    return in_fire or hit_enemy


# ---------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------
def draw_elements():
    for r in range(ROWS):
        for c in range(COLS):
            x, y = c * CELL_SIZE, r * CELL_SIZE
            color = {WALL: HARD, BOX: SOFT}.get(grid[r][c], BG)
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (30, 30, 30), (x, y, CELL_SIZE, CELL_SIZE), 1)

    # Salida
    gx, gy = GOAL[1] * CELL_SIZE, GOAL[0] * CELL_SIZE
    pygame.draw.rect(screen, EXIT, (gx + 6, gy + 6, CELL_SIZE - 12, CELL_SIZE - 12))

    for r, c, _ in bombs:
        pygame.draw.circle(screen, BOMB, (c * CELL_SIZE + 20, r * CELL_SIZE + 20), 15)

    for r, c, _ in explosions:
        pygame.draw.rect(screen, FIRE, (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for r, c, _ in enemies:
        pygame.draw.circle(screen, ENEMY, (c * CELL_SIZE + 20, r * CELL_SIZE + 20), 13)

    px, py = player_c * CELL_SIZE + 20, player_r * CELL_SIZE + 20
    pygame.draw.circle(screen, PLAYER, (px, py), 14)

    hud = font.render(f"Nivel {LEVEL_NUMBER}", True, WHITE)
    screen.blit(hud, (CELL_SIZE + 6, 8))


# ---------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------
load_level(0)
running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            new_r, new_c = player_r, player_c
            if event.key == pygame.K_UP:
                new_r -= 1
            elif event.key == pygame.K_DOWN:
                new_r += 1
            elif event.key == pygame.K_LEFT:
                new_c -= 1
            elif event.key == pygame.K_RIGHT:
                new_c += 1
            elif event.key == pygame.K_SPACE:
                place_bomb()

            if grid[new_r][new_c] == FLOOR:
                player_r, player_c = new_r, new_c

    update_bombs()
    update_explosions()
    update_enemies()

    if player_is_dead():
        die()
    elif (player_r, player_c) == GOAL:
        next_level()

    draw_elements()
    pygame.display.flip()

pygame.quit()
