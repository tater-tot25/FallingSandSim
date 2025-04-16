from baseParticle import Particle, SHADER_CACHE_SPECIFICS
from particleShaders import Still, Randomize, Shimmer
import random
import math
from gases import Steam, Smoke

class Fire(Particle):
    def __init__(self, x, y):
        super().__init__(x, y)  # Fire color
        self.type = "Fire"
        self.falling = False
        self.spawnedSmoke = False
        self.lifeTime = random.randint(100,400)
        self.setUpShader("Fire", [(237, 71, 38),(237, 164, 38)], Randomize, (5,))

    def update(self, grid):
        # Fetch color for fire animation
        self.color = self.shader.fetchColor()
        self.lifeTime -= 1
        if self.lifeTime <= 0:
            self.delete_particle(grid)
            return
        #spawn smoke
        if self.y > 0:
            if grid[self.y - 1][self.x] == None and not self.spawnedSmoke:
                particle = Smoke(self.x, self.y - 1)
                grid[self.y - 1][self.x] = particle
                self.spawnedSmoke = True
                return
        # Spread fire to flammable particles
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        for dx, dy in directions:
            if self.checkFlammable(dx, dy, grid):
                if grid[self.y + dy][self.x + dx].getType() == "Gunpowder":
                    grid[self.y + dy][self.x + dx].explode(grid, self.x + dx, self.y + dy, 5, Smoke)
                    return
                if random.randint(0, grid[self.y + dy][self.x + dx].burnChance) == 0:
                    particle = Fire(self.x + dx, self.y + dy)
                    if  grid[self.y + dy][self.x + dx] is not None:
                        grid[self.y + dy][self.x + dx].delete_and_replace(grid, particle)
                    return
                return
        # Interaction with water
        for dx, dy in directions:
            target_x = self.x + dx
            target_y = self.y + dy
            if (
                0 <= target_x < len(grid[0]) and 0 <= target_y < len(grid)
                and grid[target_y][target_x] is not None
                and grid[target_y][target_x].getType() == "Water"
            ):
                # Spawn steam at fire location
                if (random.randint(0,3) == 1):
                    grid[target_y][target_x].delete_particle(grid)
                particle = Steam(self.x, self.y)
                self.delete_and_replace(grid, particle)
                return
        # Random movement logic for fire
        if random.randint(0, 200) == 10 or self.falling:
            self.falling = True
            if self.move(0, 1, grid):  # Fall down
                return
            if self.move(-1, 1, grid):  # Fall diagonally left
                return
            if self.move(1, 1, grid):  # Fall diagonally right
                return