import multiprocessing
import os
import pygame
import math
from baseParticle import SHADER_CACHE_SPECIFICS  # Assuming this is defined elsewhere
from stationary import Rock, Wood
from fire import Fire
from sand import Gunpowder, Sand
from fluids import Acid, Water, Oil, Chaos, Void
import sharedData  # If you're still using sharedData, adapt as needed

# Constants
GRID_WIDTH, GRID_HEIGHT = 100, 100
CELL_SIZE = 6
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
EMPTY_COLOR = (0, 0, 0)
grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
brush_size = 1
frame_counter = 0
screen = None
clock = None

def startScreenUp():
    global screen, clock
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Atlantis Sandbox")
    clock = pygame.time.Clock()

def update_shaders():
    for key, value_list in SHADER_CACHE_SPECIFICS.items():
        for item in value_list:
            item.update()

def draw_grid():
    screen.fill(EMPTY_COLOR)
    for y in range(GRID_HEIGHT - 1, -1, -1):
        for x in range(GRID_WIDTH):
            particle = grid[y][x]
            if particle is not None:  # Check if particle is None
                pygame.draw.rect(screen, particle.color,
                                 (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    pygame.display.flip()

def create_particle(particle_type, x, y):
    types = {
        "sand": Sand, "water": Water, "rock": Rock, "acid": Acid,
        "wood": Wood, "fire": Fire, "gunpowder": Gunpowder, "oil": Oil,
        "chaos": Chaos, "void": Void
    }
    if particle_type in types:
        return types[particle_type](x, y)
    else:
        print(f"Warning: Unknown particle type '{particle_type}'")
        return None

def add_particle(x, y, particle_type):
    if brush_size == 1:
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and grid[y][x] is None:
            grid[y][x] = create_particle(particle_type, x, y)
    else:
        for i in range(-brush_size, brush_size + 1):
            for j in range(-brush_size, brush_size + 1):
                if math.sqrt(i**2 + j**2) <= brush_size:
                    nx, ny = x + i, y + j
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and grid[ny][nx] is None:
                        grid[ny][nx] = create_particle(particle_type, nx, ny)
    sharedData.setGrid(grid) # If you're using sharedData, adapt as needed.

def update_particle_logic(particle, grid): #New method to only update particle data.
    if particle is not None:
        return particle.update(grid) # Returns a new particle with updated data.
    return None


def update_grid_threaded(grid_queue, stop_event):
    while not stop_event.is_set():
        grid = grid_queue.get()  # Get the current grid from the queue
        new_grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)] #Create a new grid so we don't modify the original while its being drawn.

        for y in range(GRID_HEIGHT - 1, 0, -1):
            for x in range(GRID_WIDTH):
                particle = grid[y][x]
                if particle is not None:
                    new_particle = update_particle_logic(particle, grid) #Get the new particle data.
                    new_grid[y][x] = new_particle #Set the new particle data in the new grid.

        grid_queue.put(new_grid)  # Put the updated grid back in the queue

def main():
    global brush_size, frame_counter, grid
    startScreenUp()
    running = True
    particle_type = "sand"
    last_time = pygame.time.get_ticks()
    
    grid_queue = multiprocessing.Queue()
    grid_queue.put(grid)  # Initialize the queue with the initial grid
    stop_event = multiprocessing.Event()

    update_thread = multiprocessing.Process(target=update_grid_threaded, args=(grid_queue, stop_event))
    update_thread.start()

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0  # You might use dt in particle updates later

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in {pygame.K_s, pygame.K_w, pygame.K_r, pygame.K_a, pygame.K_t,
                                    pygame.K_f, pygame.K_g, pygame.K_o, pygame.K_c, pygame.K_v}:
                    particle_type = {pygame.K_s: "sand", pygame.K_w: "water", pygame.K_r: "rock",
                                        pygame.K_a: "acid", pygame.K_t: "wood", pygame.K_f: "fire",
                                        pygame.K_g: "gunpowder", pygame.K_o: "oil", pygame.K_c: "chaos",
                                        pygame.K_v: "void"}[event.key]
                elif event.key == pygame.K_UP:
                    brush_size = min(10, brush_size + 1)
                elif event.key == pygame.K_DOWN:
                    brush_size = max(1, brush_size - 1)
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            grid_x, grid_y = mx // CELL_SIZE, my // CELL_SIZE
            add_particle(grid_x, grid_y, particle_type)

        grid = grid_queue.get()
        grid_queue.put(grid) #Put the grid back in the queue so the thread can continue to work.

        update_shaders()
        draw_grid()
        clock.tick(60)
    
    stop_event.set()  # Signal the thread to stop
    update_thread.join()  # Wait for the thread to finish
    pygame.quit()

    pygame.quit()

if __name__ == "__main__":
    main()