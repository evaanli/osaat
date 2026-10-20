import pygame
import pygame.gfxdraw


# draw a smooth filled circle with an antialiased edge
def draw_smooth_circle(surface, color, center, radius):
    x, y = center
    x = round(x)
    y = round(y)
    radius = max(0, round(radius))
    if radius == 0:
        return

    draw_color = color
    if len(color) == 4 and 0 < color[3] < 255:
        # gfxdraw multiplies source alpha again on transparent surfaces
        corrected_alpha = round((color[3] * 255) ** 0.5)
        draw_color = (*color[:3], corrected_alpha)

    pygame.gfxdraw.aacircle(surface, x, y, radius, draw_color)
    pygame.gfxdraw.filled_circle(surface, x, y, radius, draw_color)
