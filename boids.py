import random
import math
from baseParticle import Particle
from particleShaders import Flock

MAX_BOIDS = 100
BOID_COUNT = 0
DIRECTIONS = [
    (0, -1), (0, 1), (-1, 0), (1, 0),  # Cardinal directions
    (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal directions
]

class Boid(Particle):
    def __init__(self, x, y, avoidance_radius=2, flock_radius=4, separation_distance=2):
        super().__init__(x, y, True)
        global BOID_COUNT
        self.type = "boid"
        self.speed = 2
        self.frameCount = 0
        self.avoidance_radius = avoidance_radius
        self.flock_radius = flock_radius
        self.separation_distance = separation_distance
        self.currentDirection = random.choice(DIRECTIONS)
        self.setUpShader("Boid", [(255, 191, 205), (255, 31, 80)], Flock)
        self.color = self.shader.fetchColor()
        self.ogColor = self.color
        self.flagForDelete = False
        BOID_COUNT += 1
        if (BOID_COUNT >= MAX_BOIDS):
            self.flagForDelete = True


    def update(self, grid):
        """Move the boid in a goal-oriented direction while avoiding obstacles and maintaining flocking behavior."""


        if self.flagForDelete:
            self.delete_particle(grid)
            return

        if self.frameCount == self.speed:
            self.frameCount = 0
            return
        self.frameCount += 1

        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        surrounded = True
        for direction in directions:
            if self.move(direction[0], direction[1], grid, "Empty") or self.move(direction[0], direction[1], grid, "Boid"):
                surrounded = False
        if surrounded:
            self.delete_particle(grid)

        boids = self.get_radius_boids(grid)
        if boids:
            theChosenBoid = random.choice(boids)
            self.color = theChosenBoid.getBoidColor()
        else:
            self.color = self.ogColor
        


        # Get flocking behaviors
        separation = self.separation(boids)
        alignment = self.alignment(boids)
        cohesion = self.cohesion(boids)

        # Combine behaviors, giving priority to separation
        dx, dy = self.currentDirection

        if separation != (0, 0):
            dx, dy = separation
        elif alignment != (0, 0):
            dx, dy = alignment
        elif cohesion != (0, 0):
            dx, dy = cohesion

        # Validate move and avoid obstacles
        valid_moves = [d for d in DIRECTIONS if self.is_valid_move(d, grid)]
        if (dx, dy) not in valid_moves:
            self.currentDirection = random.choice(valid_moves) if valid_moves else random.choice(DIRECTIONS)
            dx, dy = self.currentDirection

        # Move to the chosen direction
        self.move(dx, dy, grid)

    def is_valid_move(self, direction, grid):
        """Check if moving in the given direction is possible while avoiding obstacles."""
        dx, dy = direction
        target_x, target_y = self.x + dx, self.y + dy

        if 0 <= target_x < len(grid[0]) and 0 <= target_y < len(grid):
            return grid[target_y][target_x] is None and not self.is_obstacle_nearby(grid)
        return False

    def is_obstacle_nearby(self, grid):
        """Check for obstacles within the avoidance radius."""
        for i in range(-self.avoidance_radius, self.avoidance_radius + 1):
            for j in range(-self.avoidance_radius, self.avoidance_radius + 1):
                check_x, check_y = self.x + i, self.y + j
                if 0 <= check_x < len(grid[0]) and 0 <= check_y < len(grid):
                    if grid[check_y][check_x] is not None and not isinstance(grid[check_y][check_x], Boid):
                        return True
        return False

    def get_radius_boids(self, grid):
        """Fetch all boids in a radius."""
        boids = []
        for i in range(-self.flock_radius, self.flock_radius + 1):
            for j in range(-self.flock_radius, self.flock_radius + 1):
                check_x, check_y = self.x + i, self.y + j
                if 0 <= check_x < len(grid[0]) and 0 <= check_y < len(grid):
                    obj = grid[check_y][check_x]
                    if isinstance(obj, Boid) and obj != self:
                        boids.append(obj)
        return boids

    def separation(self, nearby_boids):
        """Steer away from nearby boids to avoid crowding."""
        steering = [0, 0]
        for boid in nearby_boids:
            dist = math.sqrt((self.x - boid.x) ** 2 + (self.y - boid.y) ** 2)
            if dist < self.separation_distance and dist > 0:
                # Move away from boid
                diff_x = self.x - boid.x
                diff_y = self.y - boid.y
                magnitude = math.sqrt(diff_x**2 + diff_y**2)
                if magnitude > 0:
                    diff_x /= magnitude
                    diff_y /= magnitude
                steering[0] += diff_x
                steering[1] += diff_y
        if steering != [0, 0]:
            return (int(steering[0]), int(steering[1]))
        return (0, 0)

    def alignment(self, nearby_boids):
        """Align direction with nearby boids."""
        avg_direction = [0, 0]
        total = len(nearby_boids)
        if total == 0:
            return (0, 0)
        for boid in nearby_boids:
            avg_direction[0] += boid.currentDirection[0]
            avg_direction[1] += boid.currentDirection[1]
        avg_direction[0] /= total
        avg_direction[1] /= total
        return (int(avg_direction[0]), int(avg_direction[1]))

    def cohesion(self, nearby_boids):
        """Move toward the center of the flock."""
        if not nearby_boids:
            return (0, 0)
        center_x = sum(boid.x for boid in nearby_boids) / len(nearby_boids)
        center_y = sum(boid.y for boid in nearby_boids) / len(nearby_boids)
        move_x = center_x - self.x
        move_y = center_y - self.y
        magnitude = math.sqrt(move_x**2 + move_y**2)
        if magnitude > 0:
            move_x /= magnitude
            move_y /= magnitude
        return (int(move_x), int(move_y))

    def getBoidColor(self):
        return self.color
    

    def delete_particle(self, grid):
        #delete this particle
        global BOID_COUNT 
        BOID_COUNT -= 1
        super().delete_particle(grid)

    def delete_and_replace(self, grid, particle):
        global BOID_COUNT
        BOID_COUNT -= 1
        super().delete_and_replace(grid, particle)