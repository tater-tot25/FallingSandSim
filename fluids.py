from baseParticle import Particle, SHADER_CACHE_SPECIFICS
from particleShaders import Still, Randomize, Shimmer
from gases import MysteriousVapor
import random
import math

LISTOFSANDS = ["Sand", "Gunpowder", "Mulch", "Gravel"]

class Fluid(Particle):
    def __init__(self, x, y, flammable=False, spread=1):
        self.spread = spread
        super().__init__(x, y, flammable)

    def update(self, grid):
        x, y = self.x, self.y  # Cache attributes
        self.color = self.shader.fetchColor()
        if y < len(grid[0]):
            below = y + 1
            if self.move(0, 1, grid, "Smoke") or self.move(0, 1, grid, "Steam"):
                self.swap(self, grid[below][x], grid)
                return True
        above = y - 1
        for sands in LISTOFSANDS:
            if self.move(0, -1, grid, sands):
                self.swap(self, grid[above][x], grid)
                return True
        if self.move(0, 1, grid):
            return True 
        move_left, move_right = self.move(-1, 1, grid), self.move(1, 1, grid)
        if move_left and move_right:
            return True if random.getrandbits(1) else self.move(1, 1, grid) 
        if random.getrandbits(1):
            if self.disperse(-1, 0, grid) or self.move(-1, 0, grid, fluid=True):
                return True
            if self.disperse(1, 0, grid) or self.move(1, 0, grid, fluid=True):
                return True
        else:
            if self.disperse(1, 0, grid) or self.move(1, 0, grid, fluid=True):
                return True
            if self.disperse(-1, 0, grid) or self.move(-1, 0, grid, fluid=True):
                return True
        return False
    
    def disperse(self, dx, dy, grid):
        if self.spread == 1 or random.randint(0, 5) == 1:
            return False
        target_x = self.x + dx * self.spread
        target_y = self.y + dy * self.spread 
        if not (0 <= target_x < len(grid[0]) and 0 <= target_y < len(grid)):
            return False
        step_range = range(0, dx * self.spread + (1 if dx > 0 else -1), (1 if dx > 0 else -1))
        for i in step_range:
            if i != 0 and grid[self.y][self.x + i] is not None:
                if grid[self.y][self.x + i].getType() != self.getType():
                    return False
        if grid[self.y][target_x] is None:
            grid[self.y][self.x] = None
            grid[self.y][target_x] = self
            self.x, self.y = target_x, target_y
            return True
        return False
        
    def fluidUnderFluid(self, grid, listOfMaterials):
        for material in listOfMaterials:
            if self.move(0, 1, grid, material):
                self.swap(self, grid[self.y + 1][self.x], grid)
        moves = []
        for i in [1, 0]:  # Check below first, then same level
            for material in listOfMaterials:
                # Check left and right movement
                if self.move(-1, i, grid, material):
                    moves.append((-1, i))
                if self.move(1, i, grid, material):
                    moves.append((1, i))
                # If valid moves exist, randomly pick one
            if i == 0:
                if self.move(-1, i, grid, self.getType()):
                    moves.append((-1, i))
                if self.move(1, i, grid, self.getType()):
                    moves.append((1, i))
        if moves:
            direction, height = random.choice(moves)
            self.swap(self, grid[self.y + height][self.x + direction], grid)
            return True  # Exit after making a move
        return False

       

"""
SUBCLASSES OF FLUID
"""

class Water(Fluid):
    def __init__(self, x, y):
        super().__init__(x, y, spread = 3)
        self.type = "Water"
        self.setUpShader("Water", [(0, 119, 190),(6, 88, 138)], Shimmer, (0.01,))

    def update(self, grid):
        super().update(grid)
        if self.move(0, 1, grid, "Acid"):  # check acid
            particle = Water(self.x, self.y + 1)
            grid[self.y + 1][self.x].delete_and_replace(grid, particle)
            return
        if self.fluidUnderFluid(grid, ["Oil"]):
            return

        
class Acid(Fluid):
    def __init__(self, x, y):
        super().__init__(x, y, flammable=True, spread = 2) 
        self.type = "Acid"
        self.burnChance = 10
        self.setUpShader("Acid", [(40, 166, 33),(93, 184, 61)], Shimmer, (0.01,))
    
    def update(self, grid):
        dissolveMats = ["Wood", "Mulch"]
        for mat in dissolveMats:
            if self.move(0, 1, grid, mat): #check for Wood
                grid[self.y + 1][self.x].delete_particle(grid)
                return
        if self.move(0, 1, grid, "Water"): #check for Water
            particle = Water(self.x, self.y)
            grid[self.y][self.x].delete_and_replace(grid, particle)
            return 
        if self.move(0, 1, grid, "Plant"):
            from gases import Grassium
            particle = Grassium(self.x, self.y + 1)
            grid[self.y + 1][self.x].delete_and_replace(grid, particle)
        if super().update(grid):
            return

class Oil(Fluid):
    def __init__(self, x, y):
        super().__init__(x, y, True, spread = 2)
        self.type = "Oil"
        self.burnChance = 2
        self.setUpShader("Oil", [(201, 116, 60),(150, 73, 23)], Shimmer, (0.02,))
    
    def update(self, grid):
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        for dx, dy in directions:
            if self.move(dx, dy, grid, "Acid"):
                particle = Slime(self.x, self.y)
                grid[self.y + dy][self.x + dx].delete_particle(grid)
                self.delete_and_replace(grid, particle)
                return
        if super().update(grid):
            return

class Slime(Fluid):
    def __init__(self, x, y):
        super().__init__(x, y) 
        self.type = "Slime"
        self.isExplosive = True
        self.setUpShader("Slime", [(218, 16, 222), (189, 21, 102)], Shimmer, (0.02,))

    def update(self, grid):
        if self.move(0, 1, grid):  # Fall down
            return 
        if random.randint(0,5) == 4: #slow how fast it moves
            super().update(grid)
            if self.fluidUnderFluid(grid, ["Oil", "Water", "Acid"]):
                return
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        mats = ["Gravel", "Sand", "Mulch"]
        for mat in mats:
            for dx, dy in directions:
                if self.move(dx, dy, grid, mat):
                    self.explode(grid, self.x, self.y, 20, MysteriousVapor)
                    return

class Chaos(Fluid):
    def __init__(self, x, y):
        super().__init__(x, y, spread = 5) 
        self.type = "Chaos"
        self.setUpShader("Chaos", [(252, 249, 136), (250, 242, 5)], Shimmer, (0.02,)) 
        from gases import Gas
        from sand import BaseSand
        from stationary import Rock, Wood
        self.gas = list(self.get_all_subclasses(Gas))
        self.sands = list(self.get_all_subclasses(BaseSand))
        self.fluids = list(self.get_all_subclasses(Fluid))
        self.fluids.remove(Chaos)
        
    def get_all_subclasses(self, cls):
            subclasses = set(cls.__subclasses__())  # Get direct subclasses
            for subclass in cls.__subclasses__():
                subclasses.update(self.get_all_subclasses(subclass))  # Recursively get subclasses
            return subclasses 

    def update(self, grid):
        from gases import Gas
        from sand import BaseSand
        from stationary import Rock, Wood
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        for dx, dy in directions:
            new_x, new_y = self.x + dx, self.y + dy
            # Ensure the new position is within bounds
            if 0 <= new_x < len(grid[0]) and 0 <= new_y < len(grid):
                # Attempt movement first
                if not self.move(dx, dy, grid, "Empty"):
                    if grid[new_y][new_x] is not None and not isinstance(grid[new_y][new_x], Chaos):
                        if isinstance(grid[new_y][new_x], Gas):
                            particle = random.choice(self.gas)(self.x+dx, self.y+dy)
                        elif isinstance(grid[new_y][new_x], BaseSand):
                            particle = random.choice(self.sands)(self.x+dx, self.y+dy)
                        elif isinstance(grid[new_y][new_x], Fluid):
                            particle = random.choice(self.fluids)(self.x+dx, self.y+dy)
                        elif isinstance(grid[new_y][new_x], Particle):
                            particle = random.choice([Rock, Wood])(self.x+dx, self.y+dy)
                        else:
                            particle = None  # Fallback case

                        # Only place the new particle if it's valid
                        if particle:
                            grid[new_y][new_x] = particle

        # Call parent class update
        if super().update(grid):
            return

class Void(Fluid): 
    def __init__(self, x, y, flammable=False, spread=3):
        super().__init__(x, y, flammable, spread)
        self.lifeTime = 0
        self.maxLifeTime = 170
        self.type = "Void"
        self.setUpShader("Void", [(0, 92, 105), (0, 223, 255)], Shimmer, (0.02,))

    def update(self, grid):
        if self.lifeTime >= self.maxLifeTime:
            self.delete_particle(grid)
            return
        self.lifeTime += 1
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        for direction in directions:
            target_x = self.x + direction[0]
            target_y = self.y + direction[1]
            if not self.move(direction[0], direction[1], grid, "Empty") and (0 <= target_x < len(grid[0]) and 0 <= target_y < len(grid)): 
                if not self.move(direction[0], direction[1], grid, "Void"):
                    grid[target_y][target_x].delete_particle(grid)
                    grid[target_y][target_x] = None
                    grid[self.y][self.x] = None
                    self.delete_particle(grid)
                    return
        if super().update(grid):
            return

    

            