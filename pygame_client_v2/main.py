"""
EDU-PARTY OOP Game Engine
Main entry point for the application.
"""
import asyncio
from game_controller import GameController


def main() -> None:
    """Main entry point."""
    game = GameController()
    asyncio.run(game.run())


if __name__ == "__main__":
    main()
