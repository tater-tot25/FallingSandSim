from baseParticle import Particle, SHADER_CACHE_SPECIFICS
from particleShaders import Still, Randomize, Shimmer
from fire import Fire
from travel import Travelling
from gases import Smoke
from stationary import Plant
import random
import math

class BaseSand(Particle):
    def __init__(self, x, y, flammable=False):
        super().__init__(x, y, flammable)
        self.velocity = [0, 0]  # Velocity in (x, y)
        self.gravity = 9.8  # Acceleration due to gravity (tweak as needed)
        self.max_fall_speed = 5  # Terminal velocity for sand

    def update(self, grid):
        # Try to move straight down first
        if self.move(0, 1, grid):  
            return True
        # If moving straight down fails, try diagonal movement
        if (random.choice([True, False])):
            if self.move(-1, 1, grid):
                return True
            if  self.move(1, 1, grid):
                return True
        else:
            if self.move(1, 1, grid):
                return True
            if  self.move(-1, 1, grid):
                return True
        return False


class Gunpowder(BaseSand):
    def __init__(self, x, y):
        super().__init__(x, y, True)  
        self.type = "Gunpowder"
        self.isExplosive = True
        self.setUpShader("Gunpowder", [(201, 190, 167), (145, 120, 112)], Still)
    

class Sand(BaseSand):
    def __init__(self, x, y):
        super().__init__(x, y)  
        self.type = "Sand"
        self.setUpShader("Sand", [(255, 232, 168), (255, 209, 82)], Still)

class Gravel(BaseSand):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.type = "Gravel"
        self.setUpShader("Gravel", [(110, 110, 110), (153, 153, 153)], Still)

class Mulch(BaseSand):
    def __init__(self, x, y):
        super().__init__(x, y, True)
        self.burnChance = 100
        self.type = "Mulch"
        self.setUpShader("Mulch", [(69, 40, 21), (156, 71, 16)], Still)

    def update(self, grid):
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        for dx, dy in directions:
            if self.move(dx, dy, grid, "Slime"):
                particle = Plant(self.x, self.y)
                grid[self.y + dy][self.x + dx].delete_and_replace(grid, particle)
                return
        super().update(grid)