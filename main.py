import pygame
import math
from baseParticle import SHADER_CACHE_SPECIFICS  # Assuming this is defined elsewhere
from stationary import Rock, Wood
from fire import Fire
from sand import Gunpowder, Sand
from fluids import Acid, Water, Oil, Chaos, Void
import sharedData

# Constants
GRID_WIDTH, GRID_HEIGHT = 100, 100
CELL_SIZE = 6
WINDOW_WIDTH, WINDOW_HEIGHT = GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE
EMPTY_COLOR = (0, 0, 0)
MAX_BRUSH_SIZE = 10
FPS = 60

grid = None
brush_size = 1
screen, clock = None, None

def start_screen():
    global screen, clock
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Atlantis Sandbox")
    clock = pygame.time.Clock()

def update_shaders():
    for value_list in SHADER_CACHE_SPECIFICS.values():
        for item in value_list:
            item.update()

def draw_grid():
    screen.fill(EMPTY_COLOR)  # Clear the screen once
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if particle := grid[y][x]:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, particle.color, rect)  # Use rect for proper size
    pygame.display.flip()

def add_particle(x, y, particle_type):
    global grid
    if brush_size == 1:
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and grid[y][x] is None:
            grid[y][x] = create_particle(particle_type, x, y)
    else:
        for i in range(-brush_size, brush_size + 1):
            for j in range(-brush_size, brush_size + 1):
                if math.hypot(i, j) <= brush_size:
                    nx, ny = x + i, y + j
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and grid[ny][nx] is None:
                        grid[ny][nx] = create_particle(particle_type, nx, ny)
    sharedData.setGrid(grid)

def create_particle(particle_type, x, y):
    particle_classes = {
        "sand": Sand, "water": Water, "rock": Rock, "acid": Acid,
        "wood": Wood, "fire": Fire, "gunpowder": Gunpowder, "oil": Oil,
        "chaos": Chaos, "void": Void
    }
    return particle_classes.get(particle_type, lambda *_: None)(x, y)

def single_core_update():
    for y in range(GRID_HEIGHT - 1, -1, -1):
        row_iter = range(GRID_WIDTH) if y % 2 == 0 else range(GRID_WIDTH - 1, -1, -1)
        for x in row_iter:
            if particle := grid[y][x]:
                particle.update(grid)

def handle_input(particle_type):
    global brush_size
    particle_map = {
        pygame.K_s: "sand", pygame.K_w: "water", pygame.K_r: "rock",
        pygame.K_a: "acid", pygame.K_t: "wood", pygame.K_f: "fire",
        pygame.K_g: "gunpowder", pygame.K_o: "oil", pygame.K_c: "chaos",
        pygame.K_v: "void"
    }
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return None
        elif event.type == pygame.KEYDOWN:
            if event.key in particle_map:
                particle_type = particle_map[event.key]
            elif event.key == pygame.K_UP:
                brush_size = min(MAX_BRUSH_SIZE, brush_size + 1)
            elif event.key == pygame.K_DOWN:
                brush_size = max(1, brush_size - 1)
    
    if pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()
        add_particle(mx // CELL_SIZE, my // CELL_SIZE, particle_type)
    
    return particle_type

def main(multi=False):
    global grid
    running, last_time = True, pygame.time.get_ticks()
    particle_type = "sand"
    while running:
        dt = (pygame.time.get_ticks() - last_time) / 1000.0
        last_time = pygame.time.get_ticks()
        new_type = handle_input(particle_type)
        if new_type is None:
            break
        particle_type = new_type
        update_shaders()
        if not multi:
            single_core_update()
        else:
            grid = sharedData.getGrid()
        draw_grid()
        clock.tick(FPS)   
    pygame.quit()


def multi_main(newgrid):
    global grid
    grid = newgrid
    start_screen()
    main(True)

if __name__ == "__main__":
    start_screen()
    grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    main()