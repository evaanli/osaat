import pygame

# player default controls: wasd

def return_movements(up=pygame.K_w, left=pygame.K_a, down=pygame.K_s, right=pygame.K_d):
    
    # collect keypresses
    keys = pygame.key.get_pressed()
    
    return [
            keys[up] * -1 + keys[down],
            keys[left] * -1 + keys[right],
    ]
