import multiprocessing
from multiprocessing import freeze_support, Process, Queue
from baseParticle import SHADER_CACHE_SPECIFICS
from stationary import Rock, Wood
from fire import Fire
from sand import Gunpowder, Sand
from fluids import Acid, Water, Oil, Chaos, Void
import math
import pygame

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
    screen.fill(EMPTY_COLOR)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if particle := grid[y][x]:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, particle.color, rect)
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

def create_particle(particle_type, x, y):
    particle_classes = {
        "sand": Sand, "water": Water, "rock": Rock, "acid": Acid,
        "wood": Wood, "fire": Fire, "gunpowder": Gunpowder, "oil": Oil,
        "chaos": Chaos, "void": Void
    }
    return particle_classes.get(particle_type, lambda *_: None)(x, y)

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

def extract_grid_section_and_update(args) -> list[list]:
    newGrid, index = args
    if index == 0:
        start_col, end_col = 0, 14
    elif index == 9:
        start_col, end_col = 85, 99
    else:
        center = (index * 10) + 5
        start_col = center - 10
        end_col = center + 9

    subgrid = [row[start_col:end_col + 1] for row in newGrid]
    num_cols = end_col - start_col + 1

    if num_cols == 20:
        update_start, update_end = 5, 14
    elif num_cols == 15 and index == 0:
        update_start, update_end = 0, 9
    elif num_cols == 15 and index == 9:
        update_start, update_end = 5, 14
    else:
        update_start, update_end = 0, 0

    for y in range(GRID_HEIGHT - 1, -1, -1):
        if y >= len(subgrid):
            continue
        for x in range(update_start, update_end + 1):
            if x >= len(subgrid[y]):
                continue
            cell = subgrid[y][x]
            if cell is not None:
                positionX = (index * 10) + x
                cell.setCoordsForLocal(positionX, index)
                cell.update(subgrid)
    return subgrid

def reassembleGrid(originalGrid, ListOfChunks, odd=False):
    oddOffsets = [5, 25, 45, 65, 85]
    evenOffsets = [0, 15, 35, 55, 75]
    offsets = oddOffsets if odd else evenOffsets
    for n in range(len(ListOfChunks)):
        chunk = ListOfChunks[n]
        start_col = offsets[n]
        chunk_width = len(chunk[0])
        end_col = start_col + chunk_width
        for row_idx in range(len(chunk)):
            for col_offset in range(chunk_width):
                originalGrid[row_idx][start_col + col_offset] = chunk[row_idx][col_offset]
    return originalGrid

# --- Multiprocessing Worker and Controller ---

def worker_loop(task_queue: Queue, result_queue: Queue):
    while True:
        task = task_queue.get()
        if task == "STOP":
            break
        newGrid, index = task
        updated_chunk = extract_grid_section_and_update((newGrid, index))
        result_queue.put((index, updated_chunk))

def collect_updates(newGrid, indices, task_queue, result_queue):
    for i in indices:
        task_queue.put((newGrid, i))
    results = {}
    for _ in indices:
        index, chunk = result_queue.get()
        results[index] = chunk
    return [results[i] for i in sorted(indices)]

# --- Main Update Loop ---

def updateGrid():
    global grid
    freeze_support()
    running = True
    particle_type = "sand"
    # Queues for worker communication
    task_queue = Queue()
    result_queue = Queue()
    odd = True
    # Spawn 10 persistent worker processes
    workers = []
    for _ in range(10):
        p = Process(target=worker_loop, args=(task_queue, result_queue))
        p.start()
        workers.append(p)
    print("Starting game loop...")
    while running:
        new_type = handle_input(particle_type)
        if new_type is None:
            running = False
            break
        particle_type = new_type
        update_shaders()
        if odd:
        # Even indices
            even_indices = [0, 2, 4, 6, 8]
            even_subgrids = collect_updates(grid, even_indices, task_queue, result_queue)
            grid = reassembleGrid(grid, even_subgrids)
        else:
        # Odd indices
            odd_indices = [1, 3, 5, 7, 9]
            odd_subgrids = collect_updates(grid, odd_indices, task_queue, result_queue)
            grid = reassembleGrid(grid, odd_subgrids, True)
        odd = not odd
        draw_grid()
        clock.tick(FPS)

    # Graceful shutdown
    for _ in workers:
        task_queue.put("STOP")
    for p in workers:
        p.join()

    print("Game loop ended.")

# --- Entry Point ---

if __name__ == "__main__":
    freeze_support()
    start_screen()
    grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    updateGrid()
