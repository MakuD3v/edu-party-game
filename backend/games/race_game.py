import asyncio
import time
from typing import Dict, Any, List
from .base import BaseGame

class RaceGame(BaseGame):
    def __init__(self, lobby):
        super().__init__(lobby)
        self.game_id = 3
        # State: player_id -> position (int 0-10)
        self.positions: Dict[str, int] = {}
        # Track finishers in order
        self.finishers: List[str] = [] 

    async def run(self):
        print(f"[GAME3] RaceGame started")
        self.is_active = True
        
        # Initialize positions for ACTIVE players
        # Note: lobby.maze_state was used before. We use local state now.
        # But we might need to sync it to lobby if lobby is used for persistent state viewing?
        # Ideally Lobby just holds Game, Game holds State.
        self.positions = {pid: 0 for pid in self.lobby.active_players}
        # Clear Lobby's maze_state just in case legacy UI depends on it (though we should update UI to rely on events)
        # Actually logic.py has `self.maze_state`. Let's assume we replace that usage.
        
        # Generate Tech Questions
        questions = self._generate_tech_questions()
        
        # Broadcast Start
        await self.lobby.broadcast({
            "type": "GAME_3_START",
            "payload": {
                "duration": 90,
                "questions": questions,
                "total_steps": 10
            }
        })
        
        # Main Loop: Wait until ALL active players finish OR timeout
        start_time = time.time()
        max_duration = 90
        
        while time.time() - start_time < max_duration:
            await asyncio.sleep(0.5)
            
            # Check completion
            active_count = len(self.lobby.active_players)
            finished_count = len(self.finishers)
            
            # If everyone finished (who is active)
            if active_count > 0 and finished_count >= active_count:
                print("[GAME3] All players finished!")
                break
                
            # Allow early exit if no active players?
            if active_count == 0:
                break

        self.is_active = False
        print(f"[GAME3] RaceGame finished. Finishers: {self.finishers}")

    async def handle_input(self, player_id: str, data: Dict[str, Any]):
        if not self.is_active:
            return
            
        # Ignore if player already finished
        if player_id in self.finishers:
            return

        is_correct = data.get("is_correct", False)
        
        # Update Position
        current_pos = self.positions.get(player_id, 0)
        new_pos = current_pos
        
        if is_correct:
            new_pos += 1
        else:
            new_pos -= 1
            
        # Clamp (0 - 10)
        if new_pos < 0: new_pos = 0
        if new_pos > 10: new_pos = 10
        
        has_moved = (new_pos != current_pos)
        self.positions[player_id] = new_pos
        
        # Send Result to Player
        if player_id in self.lobby.players:
            await self.lobby.players[player_id].websocket.send_json({
                "type": "ANSWER_RESULT",
                "payload": {
                    "correct": is_correct,
                    "new_pos": new_pos
                }
            })
            
        # Broadcast Movement if changed
        if has_moved:
            await self.lobby.broadcast({
                "type": "PLAYER_MOVED",
                "payload": {
                    "player_id": player_id,
                    "new_pos": new_pos
                }
            })
            
        # Check Finish Condition
        if new_pos >= 10 and player_id not in self.finishers:
            self.finishers.append(player_id)
            rank = len(self.finishers)
            
            # Award Points based on rank?
            # User didn't specify exact points, but "win" usually implies points.
            # Let's give: 1st=50, 2nd=30, 3rd=10, others=5?
            # Or just +1 per correct answer was already happening?
            # Wait, in Math/Typing we did +1 per correct.
            # Here we just did position.
            # Let's add a Finish Bonus.
            bonus = 0
            if rank == 1: bonus = 50
            elif rank == 2: bonus = 30
            elif rank == 3: bonus = 15
            else: bonus = 5
            
            self.lobby.player_scores[player_id] = self.lobby.player_scores.get(player_id, 0) + bonus
            
            # Notify Player of Finish
            if player_id in self.lobby.players:
                await self.lobby.players[player_id].websocket.send_json({
                    "type": "PLAYER_FINISHED",
                    "payload": {
                        "rank": rank,
                        "bonus": bonus
                    }
                })

    def _generate_tech_questions(self):
        # Using the same list from logic.py
        return [
            {"text": "Which isn't a programming language?", "a": 2, "options": ["Java", "Python", "HTML", "C++"]},
            {"text": "What does CPU stand for?", "a": 0, "options": ["Central Processing Unit", "Central Process Unit", "Computer Personal Unit", "Central Processor Unit"]},
            {"text": "Which works used for styling?", "a": 1, "options": ["HTML", "CSS", "Python", "Java"]},
            {"text": "Who created Python?", "a": 3, "options": ["Elon Musk", "Bill Gates", "Mark Zuckerberg", "Guido van Rossum"]},
            {"text": "What is 101 in binary?", "a": 0, "options": ["5", "3", "2", "6"]},
            {"text": "RAM stands for?", "a": 1, "options": ["Read Access Memory", "Random Access Memory", "Run Access Memory", "Real Access Memory"]},
            {"text": "Which keyword defines a function?", "a": 2, "options": ["func", "function", "def", "define"]},
            {"text": "Smallest unit of data?", "a": 0, "options": ["Bit", "Byte", "Kilobyte", "Megabyte"]},
            {"text": "Language for Android apps?", "a": 2, "options": ["Swift", "Ruby", "Kotlin", "PHP"]},
            {"text": "Which is a database?", "a": 3, "options": ["React", "Express", "Node", "PostgreSQL"]},
        ]
