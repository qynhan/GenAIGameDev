from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player', 'down', '0.png')).convert_alpha()
        self.rect = self.image.get_rect(center = pos)

        # movement
        self.direction = pygame.Vector2(1, 0)
        self.speed = 500

    def input(self):
        pass

    def move(self, dt):
        self.rect.center += self.direction * self.speed * dt

    def update(self, dt):
        self.input()
        self.move(dt)