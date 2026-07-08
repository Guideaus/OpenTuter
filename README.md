![OpenTuter](https://raw.githubusercontent.com/Guideaus/OpenTuter/main/res/logo.png)

**OpenTuter** — a desktop AI assistant with screen vision. It can connect to any large language model (GPT-4o, Ollama, etc.), "see" the screen through screenshots, and control the mouse/keyboard on its own.

## How it works

1. You give a task (e.g., "Open Notepad and type Hello")
2. OpenTuter captures a screenshot and sends it to the LLM with your task
3. The LLM outputs tool commands (mouse moves, clicks, keystrokes)
4. OpenTuter executes the commands
5. A new screenshot is captured and sent back — the LLM sees the result and decides what to do next
6. This loop repeats until the task is done

## Features

- **Screen vision** — screenshots are sent with every request so the AI always sees the current state
- **Autonomous control** — the AI plans, acts, observes, and iterates until completion
- **Emergency abort** — press **DEL 3 times quickly** to stop any operation
- **Any LLM** — works with any OpenAI-compatible API (GPT-4o, Qwen-VL, Claude, Ollama, vLLM, etc.)
- **First-run wizard** — guides you through API setup on first launch

## Quick start

```bash
python main.py
```

On first run, you'll be guided through API configuration. After that, just type your task.

## Project structure

```
OpenTuter/
├── main.py              # Entry point
├── core.py              # Engine: LLM calls, command execution, screen capture, abort
├── gui.py               # Interaction loop, OOBE wizard
├── agent/
│   ├── tools.mouse.json       # Mouse tool definitions for LLM
│   ├── tools.keyboard.json    # Keyboard tool definitions for LLM
│   └── controller/
│       ├── mouse.py            # Mouse command parser & executor (pyautogui)
│       └── keyboard.py         # Keyboard command parser & executor (pyautogui)
└── ugui/
    └── oobe.py           # First-time setup wizard
```

## Requirements

- Python 3.8+
- openai
- pyautogui
- pynput
- questionary
- Pillow

## Abort

Press **DEL** three times within 1.5 seconds to abort the current operation.
