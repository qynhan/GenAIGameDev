from settings import *

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()
    
    def draw(self, target_pos):
        self.offset.x = WINDOW_WIDTH // 2 - target_pos[0]
        self.offset.y = WINDOW_HEIGHT // 2 - target_pos[1]
        
        for sprite in self:
            self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)