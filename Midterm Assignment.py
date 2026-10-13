# Import a helper that reduces repetitive code in classes that hold data.
from dataclasses import dataclass

# Path lets us build a file location relative to this script instead of the
# current terminal folder, which may be a read-only directory like '/'.
from pathlib import Path


# Automatically create initialization, printing, and comparison methods.
@dataclass
class Agent:
    # A unique name used to identify this character.
    agent_id: str

    # The character's horizontal position.
    x: int

    # The character's vertical position.
    y: int

    # The character's health.
    health: int

    # True means zombie; False means human.
    is_zombie: bool


# This class holds the information needed to describe the whole game.
@dataclass
class GameState:
    # A list containing the game's Agent objects.
    agents: list[Agent]

    # The width and height of the game environment.
    width: int
    height: int

    # The current turn number. Defaults to 0 if no value is provided.
    tick: int = 0

# Tools for defining a shared interface.
from abc import ABC, abstractmethod
# ABC means Abstract Base Class.
# This class defines the methods that storage classes must implement.
class StateStore(ABC):

    # Each storage class must provide its own way to load game state.
    @abstractmethod
    def load_state(self) -> GameState:
        pass

    # Each storage class must provide its own way to save game state.
    @abstractmethod
    def save_state(self, state: GameState) -> None:
        pass


# Creates independent copies of objects, including their nested data.
from copy import deepcopy
# Inherit the load/save contract from StateStore.
class MemoryStateStore(StateStore):

    def __init__(self, initial_state: GameState):
        # Keep an independent copy of the starting game state.
        self._state = deepcopy(initial_state)

    def load_state(self) -> GameState:
        # Return a copy so changing it does not change stored data
        # until save_state() is called.
        return deepcopy(self._state)

    def save_state(self, state: GameState) -> None:
        # Replace the stored state with a copy of the supplied state.
        self._state = deepcopy(state)

# Tools for reading and writing plain text files.
# The state is saved as plain text instead of JSON so the file stays easy to read
# and does not open in a media editor like Adobe After Effects.

# This was changed to make the saved data cleaner and easier to read.
# It turns the game state into a simple summary instead of a raw dataclass printout.
def format_state(state: GameState) -> str:
    # Turn the game state into a clean text format for saving and printing.
    lines = [
        f"tick: {state.tick}",
        f"size: {state.width} x {state.height}",
        f"agents: {len(state.agents)}",
    ]

    for agent in state.agents:
        role = "Zombie" if agent.is_zombie else "Human"
        lines.append(
            f"- {agent.agent_id}: {role} | position=({agent.x}, {agent.y}) | health={agent.health}"
        )

    return "\n".join(lines) + "\n"


# This function was added to improve the terminal output.
# It prints the state in a readable layout with labels, positions, and health.
def print_state(label: str, state: GameState) -> None:
    # Print a cleaner state summary in the terminal.
    print(f"{label}:")
    print(f"  tick: {state.tick}")
    print(f"  size: {state.width} x {state.height}")
    print(f"  agents: {len(state.agents)}")

    for agent in state.agents:
        role = "Zombie" if agent.is_zombie else "Human"
        print(
            f"  - {agent.agent_id}: {role} | position=({agent.x}, {agent.y}) | health={agent.health}"
        )

    print()


# This storage class saves and loads the game state using a .txt file.
# It follows the same interface as MemoryStateStore but writes a readable file.
class TextFileStateStore(StateStore):

    def __init__(self, filename: str):
        # Remember which file this storage object uses.
        self.filename = filename

    def save_state(self, state: GameState) -> None:
        # Open the file for writing. "w" replaces its previous contents.
        with open(self.filename, "w", encoding="utf-8") as file:
            file.write(format_state(state))

    def load_state(self) -> GameState:
        # Open the existing file for reading.
        with open(self.filename, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]

        data = {"width": None, "height": None, "tick": None}
        agents = []

        for line in lines:
            if line.startswith("---") or line.startswith("tick:") is False and line.startswith("size:") is False and line.startswith("agents:") is False and line.startswith("-") is False:
                continue

            if line.startswith("tick="):
                data["tick"] = int(line.split("=", 1)[1])
            elif line.startswith("tick:"):
                data["tick"] = int(line.split(":", 1)[1].strip())
            elif line.startswith("size:"):
                size_text = line.split(":", 1)[1].strip()
                width, height = [int(part.strip()) for part in size_text.split("x")]
                data["width"] = width
                data["height"] = height
            elif line.startswith("width="):
                data["width"] = int(line.split("=", 1)[1])
            elif line.startswith("height="):
                data["height"] = int(line.split("=", 1)[1])
            elif line.startswith("agent_count="):
                pass
            elif line.startswith("agents:"):
                continue
            elif line.startswith("agent="):
                parts = line.split("=", 1)[1].split(",")
                agents.append(
                    Agent(
                        agent_id=parts[0],
                        x=int(parts[1]),
                        y=int(parts[2]),
                        health=int(parts[3]),
                        is_zombie=(parts[4] == "true"),
                    )
                )
            elif line.startswith("-"):
                # New format: "- human1: Human | position=(0, 0) | health=100"
                remainder = line.split("- ", 1)[1]
                agent_name, rest = remainder.split(": ", 1)
                role, position_part, health_part = rest.split(" | ")
                position = position_part.replace("position=", "").strip("()")
                x_str, y_str = [value.strip() for value in position.split(",")]
                health = int(health_part.split("=", 1)[1])
                agents.append(
                    Agent(
                        agent_id=agent_name,
                        x=int(x_str),
                        y=int(y_str),
                        health=health,
                        is_zombie=(role.lower() == "zombie"),
                    )
                )

        if data["width"] is None:
            data["width"] = 0
        if data["height"] is None:
            data["height"] = 0
        if data["tick"] is None:
            data["tick"] = 0

        # Rebuild and return the complete GameState object.
        return GameState(
            agents=agents,
            width=data["width"],
            height=data["height"],
            tick=data["tick"],
        )

class Simulation:

    def __init__(self, store: StateStore):
        # Remember the storage object passed into the simulation.
        self.store = store

    def step(self) -> None:
        # Load the current game state.
        state = self.store.load_state()

        # Move each living zombie one space to the right.
        for agent in state.agents:
            if agent.is_zombie and agent.health > 0:

                # Only move if the zombie will stay inside the grid.
                # For width 10, valid x positions are 0 through 9.
                if agent.x < state.width - 1:
                    agent.x += 1

        # Count this completed simulation turn.
        state.tick += 1

        # Save the updated game state.
        self.store.save_state(state)

# Run this section only when this file is executed directly.
# It will not run if another file imports this file.
if __name__ == "__main__":
    # This is the starting game state used for the demonstration.
    initial_state = GameState(
        agents=[
            Agent("human1", 0, 0, 100, False),
            Agent("zombie1", 4, 4, 100, True),
        ],
        width=10,
        height=10,
    )

    # Memory storage keeps the current state in RAM while the simulation runs.
    memory_store = MemoryStateStore(initial_state)

    # Save the report file beside this script so it is easy to locate and open.
    # Using __file__ prevents writing into read-only directories like '/'.
    report_file = Path(__file__).with_name("game_state.txt")
    storage_file = Path(__file__).with_name("game_state_storage.txt")
    file_store = TextFileStateStore(str(storage_file))
    file_store.save_state(initial_state)

    # Save the initial state before any simulation changes are applied.
    with open(report_file, "w", encoding="utf-8") as file:
        file.write("--- INITIAL STATE ---\n")
        file.write(format_state(initial_state))
        file.write("\n")

    # Print the initial state in the terminal for quick viewing.
    print_state("Initial state", initial_state)

    # Run the same simulation against both storage implementations so we can compare them.
    for store in [memory_store, file_store]:
        simulation = Simulation(store)
        for _ in range(3):
            simulation.step()

    final_memory_state = memory_store.load_state()
    final_file_state = file_store.load_state()

    # Append the final state to the report file after the simulation finishes.
    with open(report_file, "a", encoding="utf-8") as file:
        file.write("\n--- FINAL STATE ---\n")
        file.write(format_state(final_memory_state))

    # Print the final state in the terminal so both versions are easy to compare.
    print_state("Final state (memory)", final_memory_state)
    print_state("Final state (file)", final_file_state)

    # Show whether the two storage methods produced matching results.
    print("Results match:", final_memory_state == final_file_state)

