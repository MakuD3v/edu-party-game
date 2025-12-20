import asyncio
import random
import uuid
import time
from typing import Dict, Any
from .base import BaseGame

class MathGame(BaseGame):
    def __init__(self, lobby):
        super().__init__(lobby)
        self.game_id = 1
        self.current_question = None

    async def run(self):
        print(f"[GAME1] MathGame started for Lobby {self.lobby.id}")
        self.is_active = True
        
        # 1. Generate & Broadcast Question
        self.current_question = self._generate_question()
        
        # Send to all active players
        # Note: We access lobby.active_players and lobby.players. 
        # In a cleaner future, Lobby could provide a broadcast_to_active() method.
        for player_id in self.lobby.active_players:
            if player_id in self.lobby.players:
                player = self.lobby.players[player_id]
                await player.websocket.send_json({
                    "type": "NEW_QUESTION",
                    "payload": self.current_question
                })
        
        # 2. Main Loop / Timer
        # Wait for 20 seconds
        await asyncio.sleep(20)
        
        self.is_active = False
        print(f"[GAME1] MathGame finished")

    async def handle_input(self, player_id: str, data: Dict[str, Any]):
        # "answer" in data
        if not self.is_active:
            return

        user_answer = data.get("answer")
        
        # Validate input type
        try:
            val = int(user_answer)
        except (ValueError, TypeError):
            return 

        is_correct = (val == self.current_question["answer"])
        
        if is_correct:
            # Update Score via Lobby mechanisms 
            # (Direct access for now, can be abstracted later)
            self.lobby.player_scores[player_id] = self.lobby.player_scores.get(player_id, 0) + 1
            self.lobby.last_score_update[player_id] = time.time()

        # Send result back to player
        if player_id in self.lobby.players:
            await self.lobby.players[player_id].websocket.send_json({
                "type": "ANSWER_RESULT",
                "payload": {"correct": is_correct}
            })

    def _generate_question(self):
        """Generate a primary-grade math question (1-20 range)."""
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(['+', '-'])
        
        if operation == '+':
            answer = num1 + num2
            question = f"{num1} + {num2}"
        else:
            # Ensure no negative results
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
            question = f"{num1} - {num2}"
        
        return {
            'id': str(uuid.uuid4())[:8],
            'text': question,
            'answer': answer
        }
