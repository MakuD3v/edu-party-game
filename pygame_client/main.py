"""
EDU-PARTY Main Entry Point
Pygame game loop with asyncio integration for WebSocket multiplayer.
"""
import pygame
import asyncio
import sys
from game_state import game_state
from network import network
from assets import init_assets
from login_scene import LoginScene
from lobby_scene import LobbyScene
from game_scene import MathDashGame


class EDUParty:
    """Main game application."""
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Screen setup
        self.width = 1280
        self.height = 720
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EDU-PARTY - Classroom Mayhem")
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True
        
        # Initialize assets
        init_assets()
        
        # Scenes
        self.scenes = {
            "login": LoginScene(self.screen),
            "lobby": LobbyScene(self.screen),
            "game": MathDashGame(self.screen)
        }
        
        self.current_scene = self.scenes["login"]
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.current_scene.handle_event(event)
    
    def update(self, dt: float):
        """Update game state."""
        # Check for scene change
        if game_state.current_scene != self.get_current_scene_name():
            self.current_scene = self.scenes[game_state.current_scene]
        
        # Process network messages
        asyncio.create_task(self.process_network_messages())
        
        # Update current scene
        self.current_scene.update(dt)
    
    def get_current_scene_name(self) -> str:
        """Get the name of the current scene."""
        for name, scene in self.scenes.items():
            if scene == self.current_scene:
                return name
        return "login"
    
    async def process_network_messages(self):
        """Process incoming network messages."""
        try:
            while not network.incoming_queue.empty():
                message = await asyncio.wait_for(
                    network.incoming_queue.get(),
                    timeout=0.001
                )
                
                # Pass game actions to game scene
                if message.get("type") == "game_action" and isinstance(self.current_scene, MathDashGame):
                    action = message.get("action", {})
                    action["player_id"] = message.get("player_id", "")
                    self.current_scene.process_network_action(action)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"Error processing messages: {e}")
    
    def draw(self):
        """Render the current scene."""
        self.current_scene.draw()
        pygame.display.flip()
    
    async def run_async(self):
        """Main game loop with async support."""
        while self.running:
            # Delta time
            dt = self.clock.tick(self.fps) / 1000.0
            
            # Handle events
            self.handle_events()
            
            # Update
            self.update(dt)
            
            # Draw
            self.draw()
            
            # Small yield to allow async tasks to run
            await asyncio.sleep(0)
        
        # Cleanup
        if network.ws:
            await network.disconnect()
        pygame.quit()
    
    def run(self):
        """Start the game."""
        # Run the async event loop
        asyncio.run(self.run_async())


if __name__ == "__main__":
    game = EDUParty()
    game.run()
