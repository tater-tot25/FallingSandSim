from baseParticle import Particle, SHADER_CACHE_SPECIFICS
from particleShaders import Still, Randomize, Shimmer
import random

class Rock(Particle):
    def __init__(self, x, y):
        super().__init__(x, y)  # Water color
        self.type = "Rock"
        self.setUpShader("Rock", [(71, 71, 71), (80, 80, 80)], Still)
    
    def update(self, grid):
        return
    
class Wood(Particle): 
    def __init__(self, x, y):
        super().__init__(x, y, True) 
        self.type = "Wood"
        self.burnChance = 25
        self.setUpShader("Wood", [(41, 26, 23), (79, 67, 47)], Still)
    
    def update(self, grid):
        return
    
class Plant(Particle):
    def __init__(self, x, y):
        super().__init__(x, y, True) 
        self.type = "Plant"
        self.burnChance = 25
        self.setUpShader("Plant", [(76, 212, 15), (46, 125, 9)], Still)

    def update(self, grid):
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        mats =  ["Water", "Mulch"]
        for mat in mats:
            for dx, dy in directions:
                if self.move(dx, dy, grid, mat):
                    particle = Plant(self.x + dx, self.y + dy)
                    grid[self.y + dy][self.x + dx].delete_and_replace(grid, particle)
            return
        super().update(grid)
