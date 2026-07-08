# Changelog

## v1.0.0 — 2025-01-01

### Features

- **Screen Vision** — AI sees your desktop via mss screenshots, requested on demand
- **Autonomous Control** — LLM outputs mouse/keyboard commands; OpenTuter executes them in a loop until task completion
- **Any LLM** — works with any OpenAI-compatible API (GPT-4o, Qwen-VL, Claude, Ollama, vLLM)
- **Emergency Abort** — press **DEL 3 times** within 1.5 s to stop any operation
- **First-Run Wizard** — OOBE guides you through API endpoint, model, and key setup
- **System Hotkeys** — keyboard support for Win, Ctrl, Alt, Shift, Tab, Esc, Enter, etc.

### Project Structure

```
OpenTuter/
├── main.py              # Entry point
├── core.py              # Engine: LLM calls, command exec, screenshot, abort
├── gui.py               # Terminal interaction loop
├── config.json          # LLM configuration
├── agent/
│   ├── tools.mouse.json
│   ├── tools.keyboard.json
│   └── controller/
│       ├── mouse.py
│       └── keyboard.py
├── ugui/
│   └── oobe.py
└── res/
    └── logo.png
```

### Dependencies

- Python 3.8+
- openai, pyautogui, pynput, questionary, Pillow, mss

### License

MIT
