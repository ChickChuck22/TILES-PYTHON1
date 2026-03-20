from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    LOADING = auto()
    COUNTDOWN = auto()
    GAMEPLAY = auto()
    PAUSED = auto()
    GAME_OVER = auto()

class StateManager:
    def __init__(self):
        self.state = GameState.MENU
        self.context = {}

    def change_state(self, new_state, **context):
        self.state = new_state
        self.context = context

    def get_state(self):
        return self.state
