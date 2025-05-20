import multiprocessing
from multiprocessing import freeze_support, Process, Queue
from baseParticle import SHADER_CACHE_SPECIFICS
from stationary import Rock, Wood
from fire import Fire
from sand import Gunpowder, Sand
from fluids import Acid, Water, Oil, Chaos, Void
from multiprocessing import Process, Manager

GRID_WIDTH, GRID_HEIGHT = 100, 100
CHUNK_SIZE = 10


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


def multi_collect(grid, indices, pool):
    args = [(grid, i + 1) for i in indices]
    return pool.map(extract_grid_section_and_update, args)

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


def updateGrid(grid, test = False):
    freeze_support()
    task_queue = Queue()
    result_queue = Queue()
    # Spawn 10 persistent worker processes
    workers = []
    for _ in range(10):
        p = Process(target=worker_loop, args=(task_queue, result_queue))
        p.start()
        workers.append(p)
    if test:
        with multiprocessing.Pool(processes=10) as pool: #run one iteration and return the grid to check that it's correct
            even_indices = [0, 2, 4, 6, 8]
            even_subgrids = multi_collect(grid, even_indices, pool)
            grid = reassembleGrid(grid, even_subgrids)
            print("Even subgrids updated and grid reassembled")

            odd_indices = [1, 3, 5, 7, 9]
            odd_subgrids = multi_collect(grid, odd_indices, pool)
            grid = reassembleGrid(grid, odd_subgrids, True)
            print("Odd subgrids updated and grid reassembled")
            return grid
    with multiprocessing.Pool(processes=10) as pool:
        while True:
            even_indices = [0, 2, 4, 6, 8]
            even_subgrids = collect_updates(grid, even_indices, task_queue, result_queue)
            grid = reassembleGrid(grid, even_subgrids)

            # Odd indices
            odd_indices = [1, 3, 5, 7, 9]
            odd_subgrids = collect_updates(grid, odd_indices, task_queue, result_queue)
            grid = reassembleGrid(grid, odd_subgrids, True)
                #print("Odd subgrids updated and grid reassembled")

def create_particle(particle_type, x, y):
    particle_classes = {
        "sand": Sand, "water": Water, "rock": Rock, "acid": Acid,
        "wood": Wood, "fire": Fire, "gunpowder": Gunpowder, "oil": Oil,
        "chaos": Chaos, "void": Void
    }
    return particle_classes.get(particle_type, lambda *_: None)(x, y)


if __name__ == "__main__":
    freeze_support()
    grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    for y in range(GRID_WIDTH):
        for x in range(GRID_HEIGHT):
            grid[y][x] = create_particle("sand", x, y)
    updateGrid(grid)
