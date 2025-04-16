from baseParticle import Particle, SHADER_CACHE_SPECIFICS
from particleShaders import Still, Randomize, Shimmer
import random
import math

class Travelling(Particle):
    def __init__(self, x, y, dx, dy, force, oldParticle, flammable=False):
        super().__init__(x, y, flammable)
        self.type = "Travelling"
        self.oldParticle = oldParticle  

        # Normalize direction and scale with force
        magnitude = math.sqrt(dx**2 + dy**2) or 1  # Avoid division by zero
        self.velocity = [(dx / magnitude) * force, (dy / magnitude) * force]

        self.gravity = 0.2  # Reduce gravity for smoother arcs
        self.last_safe_position = (float(x), float(y))  # Store position with float precision

    def update(self, grid, dt = 0.016):
        from sand import Gravel, Mulch
        """Update position based on velocity and gravity."""
        self.velocity[1] += self.gravity * dt  # Apply gravity incrementally

        # Update position in **float values** for smooth movement
        new_x = self.last_safe_position[0] + self.velocity[0]
        new_y = self.last_safe_position[1] + self.velocity[1]

        # Convert to integer for grid positioning
        grid_x = int(new_x)
        grid_y = int(new_y)

        if self.can_move(grid_x, grid_y, grid):
            self.last_safe_position = (new_x, new_y)  # Store continuous position
            self.move(grid_x - self.x, grid_y - self.y, grid)  # Update grid
        else:
            # Collision detected → Stop and replace with old particle
            last_x, last_y = int(self.last_safe_position[0]), int(self.last_safe_position[1])
            if self.oldParticle.type == "Rock":
                self.oldParticle = Gravel(last_x, last_y)
            elif self.oldParticle.type == "Wood":
                self.oldParticle = Mulch(last_x, last_y)

            grid[self.y][self.x] = None  # Remove Travelling particle
            grid[last_y][last_x] = self.oldParticle  # Restore old particle
            self.oldParticle.x = last_x
            self.oldParticle.y = last_y

    def can_move(self, x, y, grid):
        """Check if movement is possible."""
        return 0 <= x < len(grid[0]) and 0 <= y < len(grid) and grid[y][x] is None