"""
UI Widgets Module
Contains reusable UI components like Buttons and TextInputs.
"""
import pygame

class Button:
    def __init__(self, x, y, width, height, text, color, on_click=None, text_color=(255, 255, 255), border_radius=10):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.on_click = on_click
        self.border_radius = border_radius
        self.hovered = False
        
        self.font = pygame.font.Font(None, 32)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                if self.on_click:
                    self.on_click()
                return True
        return False

    def draw(self, screen):
        # Hover effect: lighten text or darken bg
        color = self.color
        if self.hovered:
            # Simple brightness boost
            color = (min(color[0] + 20, 255), min(color[1] + 20, 255), min(color[2] + 20, 255))
        
        # Shadow/Border (optional)
        shadow_rect = self.rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=self.border_radius)
        
        pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
        
        # Border
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=self.border_radius)
        
        # Text
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class TextInput:
    def __init__(self, x, y, width, height, text="", font_size=32):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.active = False
        self.color_active = (255, 255, 255)
        self.color_passive = (200, 200, 200)
        self.font = pygame.font.Font(None, font_size)
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            return self.active
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                # Optional: trigger callback
                pass
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Limit length or chars if needed
                if len(self.text) < 20:
                    self.text += event.unicode
            return True
        return False

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, screen):
        color = self.color_active if self.active else self.color_passive
        
        # Background
        pygame.draw.rect(screen, (50, 50, 50), self.rect, border_radius=5)
        
        # Border
        pygame.draw.rect(screen, color, self.rect, 2, border_radius=5)
        
        # Text
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        
        # Clip text if too long
        screen.set_clip(self.rect)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + (self.rect.height - text_surface.get_height()) // 2))
        
        # Cursor
        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 5 + text_surface.get_width()
            cursor_y = self.rect.y + 5
            cursor_h = self.rect.height - 10
            pygame.draw.line(screen, (255, 255, 255), (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_h), 2)
            
        screen.set_clip(None)
