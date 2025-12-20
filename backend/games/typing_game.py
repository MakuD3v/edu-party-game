import asyncio
import random
import time
from typing import Dict, Any, List
from .base import BaseGame

class TypingGame(BaseGame):
    def __init__(self, lobby):
        super().__init__(lobby)
        self.game_id = 2
        self.words = []
        # We might need to track per-player progress if we want backend validation of "current word".
        # For MVP, we trust the client sends the correct word they are on?
        # Or better: simplified check. The "answer" is the typed word. We check if it is ANYWHERE in the list?
        # No, strict typing usually means sequential.
        # Let's trust client for MVP speed, or check against word list.
        # Actually logic.py checked `current_word` vs `typed_word`. 
        # The frontend sends: { word: "apple", typed: "apple" } ?
        # Let's look at app.js... app.js sends 'SUBMIT_WORD' with { word: ..., typed: ... }
        # logic.py used `check_typed_word` which checked if current == typed.

    async def run(self):
        print(f"[GAME2] TypingGame started")
        self.is_active = True
        
        self.words = self._generate_words()
        
        # Broadcast Start
        await self.lobby.broadcast({
            "type": "NEW_WORDS",
            "payload": {"words": self.words}
        })
        
        # Wait for 30 seconds (Speed Typing duration from logic.py/main.py was 30s)
        await asyncio.sleep(30)
        
        self.is_active = False 
        print(f"[GAME2] TypingGame finished")

    async def handle_input(self, player_id: str, data: Dict[str, Any]):
        if not self.is_active:
            return
            
        target_word = data.get("word", "").strip().lower()
        typed_word = data.get("typed", "").strip().lower()
        
        is_correct = (target_word == typed_word)
        
        if is_correct:
            self.lobby.player_scores[player_id] = self.lobby.player_scores.get(player_id, 0) + 1
            self.lobby.last_score_update[player_id] = time.time()
            
        if player_id in self.lobby.players:
            await self.lobby.players[player_id].websocket.send_json({
                "type": "WORD_RESULT",
                "payload": {"correct": is_correct}
            })
            
            # Send updated score immediately (Speed Typing needs live leaderboard usually)
            # Or reliance on periodic updates?
            # app.js listens for SCORE_UPDATE. logic.py didn't send it specifically on every type.
            # But let's send leaderboard update periodically or here.
            # To reduce traffic, maybe relying on a lobby background loop? 
            # For now, let's just trigger a broadcast of leaderboard!
            
            leaderboard = self.lobby.get_leaderboard()
            await self.lobby.broadcast({
                "type": "SCORE_UPDATE",
                "payload": leaderboard
            })


    def _generate_words(self, count=50) -> List[str]:
        source_words = [
            "apple", "banana", "cherry", "date", "elderberry", "fig", "grape",
            "house", "island", "jungle", "kite", "lemon", "mango", "nest",
            "ocean", "piano", "queen", "river", "sun", "tiger", "umbrella",
            "violet", "water", "xylophone", "yellow", "zebra", "cloud",
            "dream", "energy", "flower", "garden", "happy", "image", "juice",
            "king", "lion", "mouse", "night", "orange", "pencil", "quiet",
            "radio", "snake", "tree", "unicorn", "vision", "whale", "xray"
        ]
        return [random.choice(source_words) for _ in range(count)]
