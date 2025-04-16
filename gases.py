from baseParticle import Particle, SHADER_CACHE_SPECIFICS
from particleShaders import Still, Randomize, Shimmer
from boids import Boid
import random

class Gas(Particle):
    def __init__(self, x, y):
        super().__init__(x, y) 
        self.movementDelay = 2
        self.timeSinceMovement = 0
        self.lifeTime = random.randint(200, 500)
        self.isGas = True

    def update(self, grid):
        self.lifeTime -= 1
        if self.lifeTime <= 0:
            self.delete_particle(grid)
            return
        self.color = self.shader.fetchColor()

        if self.timeSinceMovement == self.movementDelay:
            self.timeSinceMovement = 0
            if self.y > 0 and self.move(0, -1, grid, "Fire"):
                self.swap(self, grid[self.y - 1][self.x], grid)
                return
            # Only rise if not at the top of the grid
            if self.y > 0 and self.move(0, -1, grid):  # Fall up
                return
            if random.choice([True, False]):
                if self.move(-1, 0, grid):  # Move left
                    return
            if self.move(1, 0, grid):  # Move right
                return
        things = ["Sand", "Gunpowder", "Mulch", "Gravel", "Water", "Acid", "Slime", "Oil", "Fire"]
        for part in things:
            if self.move(0, -1, grid, part):
                self.swap(self, grid[self.y - 1][self.x], grid) 
                return    
        else:
            self.timeSinceMovement += 1   

class Steam(Gas):
    def __init__(self, x, y):
        super().__init__(x, y) 
        self.type = "Steam"
        self.setUpShader("Steam", [(207, 207, 207), (230, 230, 230)], Shimmer, (0.01,))
    
    def update(self, grid):
        if self.lifeTime == 1 and random.randint(0,1) == 1:
            from fluids import Water
            particle = Water(self.x, self.y)
            self.delete_and_replace(grid, particle)
            return
        super().update(grid)


class Smoke(Gas):
    def __init__(self, x, y):
        super().__init__(x, y) 
        self.type = "Smoke"
        self.setUpShader("Smoke", [(110, 110, 110), (153, 153, 153)], Randomize, (2,))

class MysteriousVapor(Gas):
    def __init__(self, x, y):
        super().__init__(x, y) 
        self.type = "MysteriousVapor"
        self.setUpShader("MysteriousVapor", [(255, 0, 0), (0, 255, 208)], Shimmer, (0.02,))

    def update(self, grid):
        from stationary import Plant
        mats = ["Rock"]
        for mat in mats:
            if self.move(0, -1, grid, mat):
                if random.randint(0, 5) == 3:
                    grid[self.y - 1][self.x].delete_particle(grid)
                    return
                return
        directions = [(0, -1), (-1, 0), (1, 0)]
        mats = ["Wood", "Mulch", "Plant"]
        for mat in mats:
            for dx, dy in directions:
                if self.move(dx, dy, grid, mat):
                    particle = Plant(self.x, self.y)
                    self.delete_and_replace(grid, particle)
                    return
        super().update(grid)

class Grassium(Gas):
    def __init__(self, x, y):
        super().__init__(x, y) 
        self.type = "Grassium"
        self.lifeTime = random.randint(8000, 10000)
        self.flammable = True
        self.setUpShader("Grassium", [(69, 252, 3), (71, 255, 188)], Randomize, (1,))

    def update(self, grid):
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        for direction in directions:
            if self.move(direction[0], direction[1], grid, "Steam"): #TODO switch to another gas
                particle = Boid(self.x, self.y)
                grid[self.y + direction[1]][self.x + direction[0]].delete_particle(grid)
                self.delete_and_replace(grid, particle)
        super().update(grid)
