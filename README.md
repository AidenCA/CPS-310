# Zombie Game Simulation

Name: Aiden Atkinson

## Purpose

This project separates zombie simulation rules from state storage. It defines a shared storage interface and two working implementations: memory storage and text-file storage.

The demonstration runs the same simulation with both storage implementations, compares their final states, and writes readable initial and final summaries to a report file.

## How to run


Save the Python code as `zombie_game.py` and run:

```bash
python zombie_game.py
```

If your system uses `python3`, run `python3 zombie_game.py` instead. The program creates or replaces `game_state.txt` beside the script. That folder must allow writing.

## Classes and responsibilities

### Agent

`Agent` holds a character's ID, horizontal and vertical positions, health, and zombie status. The Boolean (True or False) `is_zombie` is `True` for a zombie and `False` for a human.

### GameState

`GameState` holds the agents, environment width and height, and current turn number, called `tick`. The default turn is zero.

`Agent` and `GameState` use `@dataclass`, which generates initialization, readable object representations, and comparisons based on their field values.

### StateStore

`StateStore` is an abstract base class defining two required methods:

- `load_state()` returns the current state as a `GameState` object.
- `save_state(state)` stores a supplied `GameState` object.

The `@abstractmethod` decorator requires subclasses to implement these methods before their instances can be created.

### MemoryStateStore

`MemoryStateStore` keeps game state in a Python object in memory. It uses `deepcopy` to copy the state and its nested agents when initializing, loading, and saving. Changes to a loaded copy do not affect stored data until `save_state()` is called.

This storage works while the program runs. Its contents are lost when the program ends.

### TextFileStateStore

`TextFileStateStore` defines the same load and save methods. Its save method uses `format_state()` to write a readable text summary to a file.

Its load method reads the readable format, converts positions, health, dimensions, and turn numbers into integers, and rebuilds the `Agent` and `GameState` objects. The demonstration uses `game_state_storage.txt` for this state and keeps the report in a separate file.

### Simulation

`Simulation` receives a storage object through its constructor. Passing this dependency into the constructor is called dependency injection.

Each simulation step:

1. Loads the state using `load_state()`.
2. Moves each living zombie one space to the right if it will remain inside the grid.
3. Increases the turn counter by one.
4. Saves the state using `save_state()`.

Humans do not move under these example rules.

## Formatting functions

`format_state(state)` returns a readable text summary containing the turn number, environment size, agent count, and each character's role, position, and health. It is used when writing the text file.

`print_state(label, state)` prints a labeled, indented summary in the terminal. It is used to display the initial and final states.

## Current demonstration

The program starts with a human at `(0, 0)` and a zombie at `(4, 4)`, both with 100 health, in a 10-by-10 environment.

It writes an initial summary to `game_state.txt` and initializes both storage options with the same starting state. It runs three simulation steps with each implementation and appends the final memory state to the report. The terminal displays the initial state and both final states. `game_state_storage.txt` contains the current state used by file storage.

The expected file contents are:

```text
--- INITIAL STATE ---
tick: 0
size: 10 x 10
agents: 2
- human1: Human | position=(0, 0) | health=100
- zombie1: Zombie | position=(4, 4) | health=100


--- FINAL STATE ---
tick: 3
size: 10 x 10
agents: 2
- human1: Human | position=(0, 0) | health=100
- zombie1: Zombie | position=(7, 4) | health=100
```

`Path(__file__).with_name("game_state.txt")` locates the output beside the script. Opening it in `"w"` mode replaces the previous run's contents; opening it in `"a"` mode appends the final summary.

The final `Results match` expression compares the final state loaded from memory with the final state loaded from text-file storage. A verification run produced `Results match: True`: both states had tick 3, the human at `(0, 0)`, and the zombie at `(7, 4)`, with both agents at 100 health.

## Why the design separates the layers

Decoupling means separating responsibilities so one implementation can change without requiring changes to another part of the program.

The simulation layer handles game rules. The storage layer handles loading and saving. `Simulation` calls only the shared `load_state()` and `save_state()` methods. It contains no file paths, file-opening operations, or text parsing.

Either storage implementation can be passed into the same simulation class. The main section demonstrates this by constructing `Simulation(store)` for each storage object. Switching storage changes the setup without changing the simulation rules.

The layers share the `Agent` and `GameState` models. The interface separates storage details from game rules; it does not remove every dependency. The main section currently writes a report directly to the file, but those report operations remain outside `Simulation`.


The demonstration starts from the initial state on every run, replacing the previous storage file and report. Memory storage disappears when the program ends; the text files remain.

