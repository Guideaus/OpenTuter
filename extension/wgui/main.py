import json
import sys
import os
import base64
from io import BytesIO
from nicegui import ui
from openai import OpenAI
import pyautogui

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import core as engine

with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

llm_cfg = cfg["llm"]
tools_cfg = cfg["tools"]
client = OpenAI(api_key=llm_cfg["api_key"], base_url=llm_cfg["base_url"])

with open(tools_cfg["mouse_path"], "r", encoding="utf-8") as f:
    mouse_tools = json.load(f)["tools"]
mouse_names = {t["name"] for t in mouse_tools}

with open(tools_cfg["keyboard_path"], "r", encoding="utf-8") as f:
    keyboard_tools = json.load(f)["tools"]
keyboard_names = {t["name"] for t in keyboard_tools}

mouse_commands = engine.load_mouse_commands()

system_prompt = f"""You are a desktop automation assistant with real-time screen vision. You control the mouse and keyboard to help the user.

## Mouse Tools
{engine.build_tool_descriptions(mouse_tools)}

## Keyboard Tools
{engine.build_tool_descriptions(keyboard_tools)}

## Rules
- You will receive a screenshot of the current screen with each message.
- Study the screen carefully, then output tool commands to accomplish the task.
- Each line = one tool command + space-separated arguments.
- After your commands execute, you'll see the updated screen.
- Keep issuing commands until the task is done.
- When the task is complete, output: FINISHED

## Example
mouse_goto 500 400
mouse_left_click
key_type Hello World
key_enter"""

messages = [{"role": "system", "content": system_prompt}]

def capture_preview():
    img = pyautogui.screenshot()
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def create_ui():
    screen_img = ui.interactive_image().classes("w-full max-w-4xl border rounded shadow")
    chat_area = ui.column().classes("w-full max-w-4xl gap-2")
    input_field = ui.input("Type your task...").classes("w-full max-w-4xl")
    status_label = ui.label().classes("text-caption text-grey-6")

    def refresh_screen():
        b64 = capture_preview()
        screen_img.set_content(f"data:image/png;base64,{b64}")

    async def send_task():
        task = input_field.value
        if not task:
            return
        input_field.value = ""
        status_label.set_text("Processing...")

        with chat_area:
            ui.chat_message(task, name="You", sent=True)

        b64 = capture_preview()
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": task},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ]
        })

        while True:
            try:
                resp = client.chat.completions.create(
                    model=llm_cfg["model"],
                    messages=messages,
                    temperature=llm_cfg.get("temperature", 0.2),
                )
                content = resp.choices[0].message.content
            except Exception as e:
                with chat_area:
                    ui.chat_message(f"Error: {e}", name="AI")
                break

            with chat_area:
                ui.chat_message(content, name="AI")
            messages.append({"role": "assistant", "content": content})

            if "FINISHED" in content:
                status_label.set_text("Done.")
                break

            for line in content.split("\n"):
                line = line.strip()
                if line:
                    engine.execute_command(line, mouse_names, keyboard_names, mouse_commands, tools_cfg)

            b64 = capture_preview()
            screen_img.set_content(f"data:image/png;base64,{b64}")

            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Commands executed. Updated screen below. Continue or output FINISHED if done."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]
            })

        status_label.set_text("")

    input_field.on("keydown.enter", send_task)
    refresh_screen()
    ui.timer(2.0, refresh_screen, active=True)
