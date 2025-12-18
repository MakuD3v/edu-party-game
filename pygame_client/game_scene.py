"""
Math Dash Game Scene
Multiplayer math quiz with platform jumping mechanics.
"""
import pygame
import random
from typing import Dict, List, Optional, Tuple
from ui_widgets import CharacterPreview
from assets import create_platform_sprite, create_timer_bell, render_crayon_text, CRAYON_RED, CRAYON_BLUE, CRAYON_GREEN, PAPER_WHITE
from game_state import game_state
from network import network
import asyncio


class MathDashGame:
    """Math Dash minigame scene."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Game state
        self.current_problem: Optional[Dict] = None
        self.platforms: List[Dict] = []  # [{"x": ..., "answer": ..., "correct": ...}]
        self.timer = 15.0
        self.round_active = False
        self.show_result = False
        self.result_timer = 0
        
        # Player positions (platform index: 0, 1, 2, or -1 for mid-air)
        self.player_positions: Dict[str, int] = {}  # player_id -> platform_index
        self.my_platform = 1  # Start on middle platform
        
        # Scores
        self.scores: Dict[str, int] = {}
        
        # Start first round as host
        if game_state.is_host:
            asyncio.create_task(self.start_new_round())
    
    async def start_new_round(self):
        """Generate new math problem and broadcast to all players."""
        # Generate problem
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(["+", "-", "*"])
        
        if operation == "+":
            correct_answer = num1 + num2
        elif operation == "-":
            correct_answer = num1 - num2
        else:  # multiplication
            correct_answer = num1 * num2
        
        # Generate wrong answers
        answers = [correct_answer]
        while len(answers) < 3:
            wrong = correct_answer + random.randint(-10, 10)
            if wrong != correct_answer and wrong not in answers:
                answers.append(wrong)
        
        random.shuffle(answers)
        correct_index = answers.index(correct_answer)
        
        # Create problem data
        problem = {
            "question": f"{num1} {operation} {num2} = ?",
            "answers": answers,
            "correct_index": correct_index,
            "correct_answer": correct_answer
        }
        
        # Broadcast to all players
        await network.send_game_action({
            "action_type": "new_round",
            "problem": problem
        })
        
        # Set locally
        self.setup_round(problem)
    
    def setup_round(self, problem: Dict):
        """Set up a new round with the given problem."""
        self.current_problem = problem
        self.timer = 15.0
        self.round_active = True
        self.show_result = False
        
        # Create platforms
        self.platforms = []
        platform_width = 200
        spacing = (self.width - 3 * platform_width) // 4
        platform_y = self.height - 150
        
        for i, answer in enumerate(problem["answers"]):
            x = spacing + i * (platform_width + spacing)
            self.platforms.append({
                "rect": pygame.Rect(x, platform_y, platform_width, 40),
                "answer": answer,
                "correct": (i == problem["correct_index"])
            })
    
    def move_to_platform(self, platform_index: int):
        """Move local player to a platform."""
        if 0 <= platform_index < 3:
            self.my_platform = platform_index
            # Broadcast movement
            asyncio.create_task(network.send_game_action({
                "action_type": "move",
                "platform": platform_index
            }))
    
    def end_round(self):
        """End the current round and show results."""
        self.round_active = False
        self.show_result = True
        self.result_timer = 3.0
        
        # Check if player is on correct platform
        if 0 <= self.my_platform < 3:
            if self.platforms[self.my_platform]["correct"]:
                # Correct!
                my_id = game_state.profile.player_id
                self.scores[my_id] = self.scores.get(my_id, 0) + 10
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        if not self.round_active:
            return
        
        # WASD movement
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.move_to_platform(max(0, self.my_platform - 1))
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.move_to_platform(min(2, self.my_platform + 1))
            elif event.key == pygame.K_1:
                self.move_to_platform(0)
            elif event.key == pygame.K_2:
                self.move_to_platform(1)
            elif event.key == pygame.K_3:
                self.move_to_platform(2)
    
    def update(self, dt: float):
        """Update game state."""
        if self.round_active:
            self.timer -= dt
            if self.timer <= 0:
                self.end_round()
        
        elif self.show_result:
            self.result_timer -= dt
            if self.result_timer <= 0:
                # Start next round
                if game_state.is_host:
                    asyncio.create_task(self.start_new_round())
    
    def process_network_action(self, action: Dict):
        """Process game action from network."""
        action_type = action.get("action_type", "")
        
        if action_type == "new_round":
            problem = action.get("problem", {})
            self.setup_round(problem)
        
        elif action_type == "move":
            player_id = action.get("player_id", "")
            platform = action.get("platform", 0)
            self.player_positions[player_id] = platform
    
    def draw(self):
        """Render the game scene."""
        # Background
        self.screen.fill(PAPER_WHITE)
        
        # Title
        title = render_crayon_text("Math Dash!", 56, (0, 0, 0))
        title_rect = title.get_rect(center=(self.width // 2, 40))
        self.screen.blit(title, title_rect)
        
        # Timer (school bell)
        bell = create_timer_bell(48)
        self.screen.blit(bell, (self.width - 100, 30))
        
        timer_font = pygame.font.Font(None, 48)
        timer_text = timer_font.render(str(int(self.timer)), True, (255, 0, 0) if self.timer < 5 else (0, 0, 0))
        self.screen.blit(timer_text, (self.width - 120, 85))
        
        # Question
        if self.current_problem:
            question_font = pygame.font.Font(None, 64)
            question_surface = question_font.render(
                self.current_problem["question"],
                True, (0, 0, 0)
            )
            question_rect = question_surface.get_rect(center=(self.width // 2, 150))
            self.screen.blit(question_surface, question_rect)
        
        # Platforms with answers
        for i, platform in enumerate(self.platforms):
            # Platform color (green if correct and showing result)
            if self.show_result:
                color = CRAYON_GREEN if platform["correct"] else CRAYON_RED
            else:
                colors = [CRAYON_RED, CRAYON_BLUE, (255, 165, 0)]  # Red, Blue, Orange
                color = colors[i]
            
            platform_surface = create_platform_sprite(
                platform["rect"].width,
                platform["rect"].height,
                color
            )
            self.screen.blit(platform_surface, platform["rect"])
            
            # Answer text
            answer_font = pygame.font.Font(None, 48)
            answer_text = answer_font.render(str(platform["answer"]), True, (255, 255, 255))
            answer_rect = answer_text.get_rect(center=platform["rect"].center)
            self.screen.blit(answer_text, answer_rect)
        
        # Draw characters on platforms
        # My character
        if 0 <= self.my_platform < 3:
            platform_rect = self.platforms[self.my_platform]["rect"]
            char_x = platform_rect.centerx - 32
            char_y = platform_rect.top - 70
            char_preview = CharacterPreview(char_x, char_y, 64)
            char_preview.draw(
                self.screen,
                game_state.profile.color,
                game_state.profile.gear
            )
        
        # Other players
        for player_id, platform_index in self.player_positions.items():
            if 0 <= platform_index < 3 and player_id in game_state.remote_players:
                player = game_state.remote_players[player_id]
                platform_rect = self.platforms[platform_index]["rect"]
                char_x = platform_rect.centerx - 32
                char_y = platform_rect.top - 70
                char_preview = CharacterPreview(char_x, char_y, 64)
                char_preview.draw(self.screen, player.color, player.gear)
                
                # Player name
                name_font = pygame.font.Font(None, 20)
                name_surface = name_font.render(player.username, True, (0, 0, 0))
                name_rect = name_surface.get_rect(center=(platform_rect.centerx, char_y - 10))
                self.screen.blit(name_surface, name_rect)
        
        # Score display
        score_y = 100
        score_font = pygame.font.Font(None, 28)
        
        # My score
        my_score = self.scores.get(game_state.profile.player_id, 0)
        my_score_text = f"Your Score: {my_score}"
        score_surface = score_font.render(my_score_text, True, (0, 0, 0))
        self.screen.blit(score_surface, (20, score_y))
        
        # Result message
        if self.show_result:
            if 0 <= self.my_platform < 3 and self.platforms[self.my_platform]["correct"]:
                result_text = "Correct! +10 points"
                result_color = (0, 200, 0)
            else:
                result_text = "Wrong answer!"
                result_color = (200, 0, 0)
            
            result = render_crayon_text(result_text, 48, result_color)
            result_rect = result.get_rect(center=(self.width // 2, 250))
            self.screen.blit(result, result_rect)
            
            # Show correct answer
            correct_answer = self.current_problem.get("correct_answer", "?")
            correct_font = pygame.font.Font(None, 36)
            correct_surface = correct_font.render(
                f"Correct answer: {correct_answer}",
                True, (0, 150, 0)
            )
            correct_rect = correct_surface.get_rect(center=(self.width // 2, 300))
            self.screen.blit(correct_surface, correct_rect)
        
        # Instructions
        if self.round_active:
            inst_font = pygame.font.Font(None, 24)
            inst_text = "Use A/D or Arrow Keys or 1/2/3 to move between platforms"
            inst_surface = inst_font.render(inst_text, True, (100, 100, 100))
            inst_rect = inst_surface.get_rect(center=(self.width // 2, self.height - 30))
            self.screen.blit(inst_surface, inst_rect)
