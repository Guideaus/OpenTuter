import json
import sys
import time
import base64
import threading
from io import BytesIO
import pyautogui
from openai import OpenAI
from pynput import keyboard as pynput_kb
from agent.controller.keyboard import agent_task_handler as keyboard_handler

pyautogui.PAUSE = 0.05

class AbortController:
    def __init__(self, window=1.5):
        self.aborted = False
        self._lock = threading.Lock()
        self._presses = []
        self._window = window
        self._listener = None

    def _on_press(self, key):
        try:
            if key == pynput_kb.Key.delete:
                now = time.time()
                with self._lock:
                    self._presses = [t for t in self._presses if now - t < self._window]
                    self._presses.append(now)
                    if len(self._presses) >= 3:
                        self.aborted = True
        except:
            pass

    def start(self):
        if self._listener is None:
            self._listener = pynput_kb.Listener(on_press=self._on_press)
            self._listener.daemon = True
            self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

def capture_screen_base64():
    img = pyautogui.screenshot()
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def build_tool_descriptions(tools):
    lines = []
    for t in tools:
        props = t["parameters"].get("properties", {})
        params = ", ".join(f"{k}" for k in props)
        lines.append(f"  {t['name']}({params}) - {t['description']}")
    return "\n".join(lines)

def execute_command(line, mouse_names, keyboard_names, mouse_commands, tools_cfg):
    line = line.strip()
    if not line:
        return
    parts = line.split()
    name = parts[0]
    args = parts[1:]
    if name in mouse_names and tools_cfg.get("enable_mouse", True):
        fn = mouse_commands.get(name)
        if fn:
            fn(args)
    elif name in keyboard_names and tools_cfg.get("enable_keyboard", True):
        keyboard_handler(line)
    elif name in ("press", "click"):
        keyboard_handler(line)

def ask_and_execute(user_input, messages, client, llm_cfg, mouse_names, keyboard_names, mouse_commands, tools_cfg):
    messages.append({"role": "user", "content": user_input})
    try:
        resp = client.chat.completions.create(
            model=llm_cfg["model"],
            messages=messages,
            temperature=llm_cfg.get("temperature", 0.2),
        )
        content = resp.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"
    messages.append({"role": "assistant", "content": content})
    for line in content.split("\n"):
        execute_command(line, mouse_names, keyboard_names, mouse_commands, tools_cfg)
    return content

def load_mouse_commands():
    return {
        "mouse_goto": lambda args: pyautogui.moveTo(int(args[0]), int(args[1])),
        "mouse_left_click": lambda args: pyautogui.click(button="left"),
        "mouse_right_click": lambda args: pyautogui.click(button="right"),
        "mouse_middle_click": lambda args: pyautogui.click(button="middle"),
        "mouse_left_click_at": lambda args: pyautogui.click(int(args[0]), int(args[1]), button="left"),
        "mouse_right_click_at": lambda args: pyautogui.click(int(args[0]), int(args[1]), button="right"),
        "mouse_middle_click_at": lambda args: pyautogui.click(int(args[0]), int(args[1]), button="middle"),
        "mouse_double_left_click": lambda args: pyautogui.doubleClick(button="left"),
        "mouse_double_left_click_at": lambda args: pyautogui.doubleClick(int(args[0]), int(args[1])),
        "mouse_press": lambda args: pyautogui.mouseDown(button=args[0]),
        "mouse_release": lambda args: pyautogui.mouseUp(button=args[0]),
        "mouse_drag": lambda args: pyautogui.drag(int(args[2]) - int(args[0]), int(args[3]) - int(args[1]), duration=0.2),
        "mouse_scroll": lambda args: pyautogui.scroll(int(args[0])),
        "mouse_hover": lambda args: (pyautogui.moveTo(int(args[0]), int(args[1])), time.sleep(int(args[2]) / 1000)),
    }
