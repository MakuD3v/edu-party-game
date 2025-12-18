"""
MathDash Class - Educational minigame with arithmetic problems.
Handles problem generation, platform creation, and collision detection.
"""
import pygame
import random
from typing import Any
from constants import CHALKBOARD_DARK, CHALK_WHITE, SCHOOL_BUS_YELLOW, STUDENT_RED, STUDENT_BLUE, STUDENT_GREEN


class AnswerPlatform:
    """Represents a platform with an answer choice."""
    
    def __init__(self, x: int, y: int, width: int, height: int, answer: int, correct: bool):
        """Initialize answer platform.
        
        Args:
            x: X position
            y: Y position
            width: Platform width
            height: Platform height
            answer: The answer value on this platform
            correct: Whether this is the correct answer
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.answer: int = answer
        self.correct: bool = correct
        self._color: tuple[int, int, int] = STUDENT_BLUE
    
    def set_color(self, color: tuple[int, int, int]) -> None:
        """Set platform color."""
        self._color = color
    
    def render(self, surface: pygame.Surface, show_result: bool = False) -> None:
        """Render the platform.
        
        Args:
            surface: Pygame surface to draw on
            show_result: If True, show green/red for correct/incorrect
        """
        # Color based on state
        if show_result:
            color = STUDENT_GREEN if self.correct else STUDENT_RED
        else:
            color = self._color
        
        # Draw platform
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, CHALK_WHITE, self.rect, 3, border_radius=10)
        
        # Highlight for 3D effect
        highlight = tuple(min(255, c + 30) for c in color)
        highlight_rect = pygame.Rect(
            self.rect.x + 5,
            self.rect.y + 5,
            self.rect.width - 10,
            self.rect.height // 2
        )
        pygame.draw.rect(surface, highlight, highlight_rect, border_radius=5)
        
        # Draw answer text
        font = pygame.font.Font(None, 48)
        text = font.render(str(self.answer), True, CHALK_WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is on this platform.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if point is within platform bounds
        """
        return self.rect.collidepoint(int(x), int(y))


class MathDash:
    """Educational math minigame."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize MathDash game.
        
        Args:
            screen_width: Game screen width
            screen_height: Game screen height
        """
        self._screen_width: int = screen_width
        self._screen_height: int = screen_height
        
        self._problem: str = ""
        self._correct_answer: int = 0
        self._platforms: list[AnswerPlatform] = []
        self._timer: float = 15.0
        self._active: bool = False
        self._show_result: bool = False
        self._result_timer: float = 0.0
        
        # Player platform tracking
        self._player_platforms: dict[str, int] = {}  # student_id -> platform_index
    
    @property
    def active(self) -> bool:
        """Check if game is active."""
        return self._active
    
    @property
    def problem(self) -> str:
        """Get current problem string."""
        return self._problem
    
    @property
    def timer(self) -> float:
        """Get remaining time."""
        return self._timer
    
    def generate_problem(self) -> dict[str, Any]:
        """Generate a random arithmetic problem.
        
        Returns:
            Dictionary with problem data
        """
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(["+", "-", "*"])
        
        if operation == "+":
            correct = num1 + num2
        elif operation == "-":
            correct = num1 - num2
        else:  # multiplication
            correct = num1 * num2
        
        # Generate wrong answers
        answers = [correct]
        while len(answers) < 3:
            wrong = correct + random.randint(-10, 10)
            if wrong > 0 and wrong not in answers:
                answers.append(wrong)
        
        random.shuffle(answers)
        correct_index = answers.index(correct)
        
        problem_data = {
            "question": f"{num1} {operation} {num2} = ?",
            "answers": answers,
            "correct_index": correct_index,
            "correct_answer": correct
        }
        
        self._setup_round(problem_data)
        return problem_data
    
    def _setup_round(self, problem_data: dict[str, Any]) -> None:
        """Set up a new round with given problem.
        
        Args:
            problem_data: Problem data dictionary
        """
        self._problem = problem_data["question"]
        self._correct_answer = problem_data["correct_answer"]
        self._timer = 15.0
        self._active = True
        self._show_result = False
        self._player_platforms.clear()
        
        # Create platforms
        self._platforms.clear()
        platform_width = 200
        platform_height = 40
        spacing = (self._screen_width - 3 * platform_width) // 4
        platform_y = self._screen_height - 150
        
        colors = [STUDENT_RED, STUDENT_BLUE, (255, 165, 0)]  # Red, Blue, Orange
        
        for i, answer in enumerate(problem_data["answers"]):
            x = spacing + i * (platform_width + spacing)
            platform = AnswerPlatform(
                x, platform_y, platform_width, platform_height,
                answer, i == problem_data["correct_index"]
            )
            platform.set_color(colors[i])
            self._platforms.append(platform)
    
    def set_player_platform(self, student_id: str, platform_index: int) -> None:
        """Set which platform a player is on.
        
        Args:
            student_id: Student ID
            platform_index: Platform index (0-2, or -1 for none)
        """
        if platform_index == -1:
            self._player_platforms.pop(student_id, None)
        else:
            self._player_platforms[student_id] = platform_index
    
    def get_player_platform(self, student_id: str) -> int:
        """Get platform index for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            Platform index or -1 if not on a platform
        """
        return self._player_platforms.get(student_id, -1)
    
    def check_collision(self, x: float, y: float) -> int:
        """Check which platform a point is on.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Platform index (0-2) or -1 if not on any platform
        """
        for i, platform in enumerate(self._platforms):
            if platform.contains_point(x, y):
                return i
        return -1
    
    def is_answer_correct(self, platform_index: int) -> bool:
        """Check if a platform has the correct answer.
        
        Args:
            platform_index: Platform index to check
            
        Returns:
            True if platform has correct answer
        """
        if 0 <= platform_index < len(self._platforms):
            return self._platforms[platform_index].correct
        return False
    
    def end_round(self) -> None:
        """End the current round and show results."""
        self._active = False
        self._show_result = True
        self._result_timer = 3.0
    
    def update(self, dt: float) -> bool:
        """Update game state.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            True if round just ended, False otherwise
        """
        round_ended = False
        
        if self._active:
            self._timer -= dt
            if self._timer <= 0:
                self.end_round()
                round_ended = True
        
        elif self._show_result:
            self._result_timer -= dt
            if self._result_timer <= 0:
                self._show_result = False
                # Ready for next round
        
        return round_ended
    
    def render(self, surface: pygame.Surface) -> None:
        """Render the math dash game.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Problem text
        if self._problem:
            font = pygame.font.Font(None, 64)
            text = font.render(self._problem, True, CHALK_WHITE)
            text_rect = text.get_rect(center=(self._screen_width // 2, 150))
            surface.blit(text, text_rect)
        
        # Timer
        timer_font = pygame.font.Font(None, 48)
        timer_color = STUDENT_RED if self._timer < 5 else SCHOOL_BUS_YELLOW
        timer_text = timer_font.render(f"Time: {int(self._timer)}", True, timer_color)
        surface.blit(timer_text, (self._screen_width - 200, 30))
        
        # Platforms
        for platform in self._platforms:
            platform.render(surface, self._show_result)
        
        # Result message
        if self._show_result:
            result_font = pygame.font.Font(None, 56)
            result_text = f"Correct answer: {self._correct_answer}"
            text = result_font.render(result_text, True, STUDENT_GREEN)
            text_rect = text.get_rect(center=(self._screen_width // 2, 250))
            surface.blit(text, text_rect)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"MathDash(problem={self._problem}, timer={self._timer:.1f}, active={self._active})"
