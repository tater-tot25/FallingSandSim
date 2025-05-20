import random
from particleShaders import Randomize, Shimmer, Still
import math

MAX_SHADER_VARIANTS = 5
SHADER_CACHE = {}
SHADER_CACHE_SPECIFICS = {}

# Base Particle Class
class Particle:
    def __init__(self, x, y, flammable = False):
        self.x = x
        self.y = y
        self.shader = None
        self.color = (0,0,0)
        self.type = "generic"  # Default type for particles
        self.flammable = flammable
        self.velocity = [0,0]
        self.gravity = 9.8
        self.burnChance = 0
        self.isExplosive = False
        self.isGas = False

    def setUpShader(self, name, colors, shader_class, shader_args=None):
        if shader_args is None:
            shader_args = ()  # Default empty tuple
        # Check if a new shader is needed
        if self.shaderCache(name):
            SHADER_CACHE_SPECIFICS[name].append(shader_class(colors, *shader_args))  # Dynamically instantiate shader
        # Pick a random shader from cache
        self.shader = random.choice(SHADER_CACHE_SPECIFICS[name])
        self.color = self.shader.fetchColor()

    def convertToLocal(self, columnOffset):
        self.x = self.x - (columnOffset * 10)

    def convertToGlobal(self, columnOffset):
        self.x = self.x + (columnOffset * 10)

    def setCoordsForLocal(self, positionX, columnOffset):
        self.x = positionX - (columnOffset * 10)

    def getLoc(self):
        return (self.x, self.y)

    def shaderCache(self, particleType):
        if particleType in SHADER_CACHE:
            numOfVariants = SHADER_CACHE[particleType]
            if numOfVariants < MAX_SHADER_VARIANTS:
                SHADER_CACHE[particleType] += 1
                return True
            else:
                return False
        else:
            SHADER_CACHE[particleType] = 0
            SHADER_CACHE_SPECIFICS[particleType] = []
            return True

    def update(self, grid, dt = 1):
        pass

    def getType(self):
        return self.type

    def getFlammable(self):
        return self.flammable

    def move(self, dx, dy, grid, checkMat=None, fluid=False):
        """Move the particle if the target cell is empty or matches conditions."""
        target_x, target_y = self.x + dx, self.y + dy
        if not (0 <= target_x < len(grid[0]) and 0 <= target_y < len(grid)):
            return False  # Out of bounds
        target_cell = grid[target_y][target_x]
        if checkMat == "Empty":
            return target_cell is None  # Only return if the cell is empty
        if target_cell is None:
            if checkMat is None:
                grid[self.y][self.x], grid[target_y][target_x] = None, self
                self.x, self.y = target_x, target_y
                return True
            return False
        if fluid and target_cell.getType() == self.getType():
            return checkMat is None
        return checkMat is not None and target_cell.getType() == checkMat
    
    def checkFlammable(self, dx, dy, grid):
        target_x = self.x + dx
        target_y = self.y + dy
        if 0 <= target_x < len(grid[0]) and 0 <= target_y < len(grid):
            if grid[target_y][target_x] != None:
                if grid[target_y][target_x].getFlammable():
                    return True
        return False
    
    def swap(self, particleOne, particleTwo, grid):
        """Swap the positions of two particles on the grid."""
        if particleOne is None or particleTwo is None:
            return  # One or both particles are missing, do nothing
        
        # Swap their positions in the grid
        grid[particleOne.y][particleOne.x], grid[particleTwo.y][particleTwo.x] = grid[particleTwo.y][particleTwo.x], grid[particleOne.y][particleOne.x]
        
        # Swap their coordinates
        particleOne.x, particleTwo.x = particleTwo.x, particleOne.x
        particleOne.y, particleTwo.y = particleTwo.y, particleOne.y
        return
    
    def delete_particle(self, grid):
        #delete this particle
        grid[self.y][self.x] = None  # Remove it from the grid
        del self  # Explicitly delete the particle object (optional)

    def delete_and_replace(self, grid, particle): # same as above, but we replace the particle with a new one
        grid[self.y][self.x] = particle  # Remove it from the grid
        del self

    def explode(self, grid, x, y, radius, emission):
        from gases import Smoke
        from travel import Travelling
        from fire import Fire
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                target_x = x + i
                target_y = y + j

                # Check if target is within bounds
                if 0 <= target_x < len(grid[0]) and 0 <= target_y < len(grid):
                    distance = math.sqrt(i**2 + j**2)  # Distance from explosion center

                    if distance <= radius:
                        if grid[target_y][target_x] is not None:
                            old_particle = grid[target_y][target_x]  # Store old particle
                            grid[target_y][target_x] = None  # Clear spot
                            # Only fling particles that aren't Gunpowder or other explosives
                            if old_particle.isExplosive == False and old_particle.isGas == False and old_particle.getType() != "Fire":
                                if random.randint(0,2) == 1:
                                    force = random.uniform(0.5, 1.5)  # Random explosion force
                                    dx = i / distance  # Normalize push direction
                                    dy = j / distance
                                    grid[target_y][target_x] = Travelling(target_x, target_y, dx, dy, force, old_particle)

                        # Add fire at the perimeter
                        if radius - 0.5 <= distance <= radius + 0.5:  
                            if grid[target_y][target_x] is None:
                                grid[target_y][target_x] = Fire(target_x, target_y)  # Spawn fire particle

                        # Push smoke outward
                        if distance > 1:
                            dx = int(i / distance * 2)  
                            dy = int(j / distance * 2)
                            new_x = target_x + dx
                            new_y = target_y + dy
                            if 0 <= new_x < len(grid[0]) and 0 <= new_y < len(grid):
                                if grid[new_y][new_x] is None:
                                    grid[new_y][new_x] = emission(new_x, new_y)  # Spawn smoke