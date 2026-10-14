import pygame

# player 1 controls: wasd
# player 2 controls: arrow keys

def return_movements():
    # collect keypresses
    keys = pygame.key.get_pressed()
    
    return [
        # player 1
        [
            keys[pygame.K_w] * -1 + keys[pygame.K_s],
            keys[pygame.K_a] * -1 + keys[pygame.K_d],
        ],
        # player 2
        [
            keys[pygame.K_UP] * -1 + keys[pygame.K_DOWN],
            keys[pygame.K_LEFT] * -1 + keys[pygame.K_RIGHT],
        ]
    ]
