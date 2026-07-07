import json
import os
import sys
import threading
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import core as engine

app = Flask(__name__, template_folder="templates", static_folder="static")

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

system_prompt = f"""You are a desktop automation assistant with real-time screen vision.

## Mouse Tools
{engine.build_tool_descriptions(mouse_tools)}

## Keyboard Tools
{engine.build_tool_descriptions(keyboard_tools)}

## Rules
- You will receive a screenshot with each message.
- Output one tool command per line.
- After commands execute, you'll see the updated screen.
- Keep going until the task is done.
- When done, output: FINISHED

## Example
mouse_goto 500 400
mouse_left_click
key_type Hello World
key_enter"""

messages = [{"role": "system", "content": system_prompt}]
_msg_lock = threading.Lock()

PLUGINS = [
    {
        "name": "wgui",
        "title": "Web GUI",
        "description": "A web-based control panel for OpenTuter. Chat with the AI, see the live screen, and control your desktop from a browser.",
        "author": "OpenTuter",
        "version": "1.0.0",
    },
]

@app.route("/")
def store():
    return render_template("store.html", plugins=PLUGINS)

@app.route("/wgui")
def wgui():
    return render_template("wgui.html")

@app.route("/api/screenshot")
def api_screenshot():
    b64 = engine.capture_screen_base64(scale=0.5, fmt="JPEG", quality=70)
    return jsonify({"image": b64})

@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.get_json()
    task = data.get("task", "").strip()
    if not task:
        return jsonify({"error": "empty task"}), 400

    with _msg_lock:
        b64 = engine.capture_screen_base64(scale=1.0, fmt="PNG")
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": task},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ]
        })

        try:
            resp = client.chat.completions.create(
                model=llm_cfg["model"],
                messages=messages,
                temperature=llm_cfg.get("temperature", 0.2),
            )
            content = resp.choices[0].message.content
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        messages.append({"role": "assistant", "content": content})

        for line in content.split("\n"):
            line = line.strip()
            if line:
                engine.execute_command(line, mouse_names, keyboard_names, mouse_commands, tools_cfg)

        b64_after = engine.capture_screen_base64(scale=1.0, fmt="PNG")

        if "FINISHED" not in content:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Commands executed. Updated screen below. Continue or output FINISHED if done."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_after}"}}
                ]
            })

    return jsonify({"reply": content, "screenshot": b64_after})

def main():
    app.run(host="0.0.0.0", port=8080, debug=False)

if __name__ == "__main__":
    main()
