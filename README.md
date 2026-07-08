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

### Usage

1. **First run** — the OOBE wizard will ask for your API endpoint, model name, and API key
2. **Give a task** — type your goal in natural language (e.g., "open calculator and compute 15 * 7")
3. **AI works** — OpenTuter captures a screenshot, the LLM plans actions, executes mouse/keyboard commands, then captures another screenshot to verify
4. **Done** — the AI signals completion; you can give the next task
5. **Abort** — press **DEL three times quickly** to interrupt any running operation

### Configuration

Edit `config.json` manually at any time:

```json
{
  "api_base": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "api_key": "sk-..."
}
```

Supports any OpenAI-compatible endpoint:
- **GPT-4o** — `https://api.openai.com/v1`
- **Ollama** — `http://localhost:11434/v1` (use any key like `ollama`)
- **vLLM** — `http://localhost:8000/v1`
- **Qwen-VL / Claude** — their respective OpenAI-compatible endpoints

## Project structure

```
OpenTuter/
├── main.py              # Entry point (launches gui.main())
├── core.py              # Engine: LLM calls, command execution, screen capture, abort
├── gui.py               # Terminal interaction loop
├── config.json          # LLM configuration (api_base, model, api_key)
├── res/
│   └── logo.png         # Logo
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
- mss

## Abort

Press **DEL** three times within 1.5 seconds to abort the current operation.
