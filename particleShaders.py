import random

class ParticleShader:

    def __init__(self, colors):
        self.colorRange = colors
        self.currentColor = self.pickColorInRange()

    def update(self):
        pass

    def pickColorInRange(self): #returns a tuple of RGB values from the preset colors
        color1 = self.colorRange[0]
        color2 = self.colorRange[1]
        r = random.randint(min(color1[0], color2[0]), max(color1[0], color2[0]))
        g = random.randint(min(color1[1], color2[1]), max(color1[1], color2[1]))
        b = random.randint(min(color1[2], color2[2]), max(color1[2], color2[2]))
        return (r, g, b)
    
        
    def fetchColor(self):
        return self.currentColor

class Shimmer(ParticleShader):

    def __init__(self, colors, speed):
        super().__init__(colors)
        self.speed = speed
        self.direction = 1  # 1 for forward (towards color2), -1 for backward (towards color1)

    def calculate_next_color(self, speed):
        """
        Calculate the next color based on the direction and speed.

        :param speed: The speed of transition between the colors.
        :return: The next color as a tuple (r, g, b).
        """
        # Calculate the new color components
        next_r = self.currentColor[0] + self.direction * speed * (self.colorRange[1][0] - self.colorRange[0][0])
        next_g = self.currentColor[1] + self.direction * speed * (self.colorRange[1][1] - self.colorRange[0][1])
        next_b = self.currentColor[2] + self.direction * speed * (self.colorRange[1][2] - self.colorRange[0][2])

        # Clamp the color values between the min and max of the two target colors
        next_r = min(max(next_r, min(self.colorRange[0][0], self.colorRange[1][0])), max(self.colorRange[0][0], self.colorRange[1][0]))
        next_g = min(max(next_g, min(self.colorRange[0][1], self.colorRange[1][1])), max(self.colorRange[0][1], self.colorRange[1][1]))
        next_b = min(max(next_b, min(self.colorRange[0][2], self.colorRange[1][2])), max(self.colorRange[0][2], self.colorRange[1][2]))

        # Update the current color
        self.currentColor = (next_r, next_g, next_b)

        # Reverse direction if we reach the target color
        if self.direction == 1 and self.currentColor == self.colorRange[1]:
            self.direction = -1
        elif self.direction == -1 and self.currentColor == self.colorRange[0]:
            self.direction = 1

        return self.currentColor

    def update(self):
        self.calculate_next_color(self.speed)

class Randomize(ParticleShader):

    def __init__(self, colors, speed):
        super().__init__(colors) 
        self.speed = speed 
        self.timeElapsed = 0
        
    def update(self):
        self.timeElapsed += 1
        if self.timeElapsed / self.speed == 1:
            self.timeElapsed = 0
            self.currentColor = self.pickColorInRange()
        
class Still(ParticleShader):

    def __init__(self, colors):
        super().__init__(colors)  
        pass

class Flock(ParticleShader):

    def __init__(self, colors):
        super().__init__(colors)
        self.frameCount = 0
        self.resetThreshold = 400
        pass

    def update(self):
        if self.frameCount == self.resetThreshold:
            self.currentColor = self.pickColorInRange()
            self.frameCount = 0
        self.frameCount += 1
        