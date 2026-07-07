import json
import os
import sys
import threading
from flask import Flask, render_template, request, jsonify, redirect
from openai import OpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import core as engine

app = Flask(__name__, template_folder="templates", static_folder="static")

_cfg = None
_llm_cfg = None
_tools_cfg = None
_client = None
_mouse_names = None
_keyboard_names = None
_mouse_commands = None
_mouse_tools_data = None
_keyboard_tools_data = None
_messages = []
_msg_lock = threading.Lock()
_system_prompt = None

PLUGINS = [
    {
        "name": "wgui",
        "title": "Web GUI",
        "description": "A web-based control panel for OpenTuter. Chat with the AI, see the live screen, and control your desktop from a browser.",
        "author": "OpenTuter",
        "version": "1.0.0",
    },
]

API_PROVIDERS = {
    "OpenAI": "https://api.openai.com/v1",
    "Azure OpenAI": "https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions",
    "Anthropic Claude": "https://api.anthropic.com",
    "Google Gemini": "https://generativelanguage.googleapis.com",
    "Alibaba Qwen": "https://dashscope.aliyuncs.com/api/v1",
    "Baidu ERNIE": "https://qianfan.baidubce.com/v2",
    "Zhipu GLM": "https://open.bigmodel.cn/api/paas/v4",
    "ByteDance Doubao": "https://ark.cn-beijing.volces.com/api/v3",
    "Meta Llama (Ollama)": "http://localhost:11434/v1",
    "Local Ollama Model": "http://localhost:11434/v1",
    "Custom API Endpoint": "",
}

def config_complete():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            d = json.load(f)
        llm = d["llm"]
        return all(llm.get(k, "").strip() for k in ["api_key", "base_url", "model"])
    except:
        return False

def ensure_loaded():
    global _cfg, _llm_cfg, _tools_cfg, _client, _mouse_names, _keyboard_names, _mouse_commands, _messages, _system_prompt, _mouse_tools_data, _keyboard_tools_data
    if _cfg is not None:
        return True
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            _cfg = json.load(f)
        _llm_cfg = _cfg["llm"]
        _tools_cfg = _cfg["tools"]

        api_key = _llm_cfg.get("api_key", "").strip()
        base_url = _llm_cfg.get("base_url", "").strip()
        is_local = any(h in base_url for h in ("localhost", "127.0.0.1"))
        if not api_key and is_local:
            api_key = "not-needed"

        _client = OpenAI(api_key=api_key, base_url=base_url)

        with open(_tools_cfg["mouse_path"], "r", encoding="utf-8") as f:
            _mouse_tools_data = json.load(f)["tools"]
            _mouse_names = {t["name"] for t in _mouse_tools_data}
        with open(_tools_cfg["keyboard_path"], "r", encoding="utf-8") as f:
            _keyboard_tools_data = json.load(f)["tools"]
            _keyboard_names = {t["name"] for t in _keyboard_tools_data}

        _mouse_commands = engine.load_mouse_commands()

        _system_prompt = f"""You are a desktop automation assistant with real-time screen vision.

## Mouse Tools
{engine.build_tool_descriptions(_mouse_tools_data)}

## Keyboard Tools
{engine.build_tool_descriptions(_keyboard_tools_data)}

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

        _messages.clear()
        _messages.append({"role": "system", "content": _system_prompt})
        return True
    except Exception as e:
        print(f"[server] init error: {e}", file=sys.stderr)
        return False

@app.route("/api/config_status")
def api_config_status():
    return jsonify({"configured": config_complete()})

@app.route("/api/providers")
def api_providers():
    return jsonify(API_PROVIDERS)

@app.route("/api/save_config", methods=["POST"])
def api_save_config():
    data = request.get_json()
    provider = data.get("provider", "")
    api_key = data.get("api_key", "").strip()
    model = data.get("model", "").strip()
    base_url = data.get("base_url", "").strip()

    if not provider and not base_url:
        return jsonify({"error": "Provider or base URL required"}), 400

    if provider and provider in API_PROVIDERS:
        base_url = API_PROVIDERS[provider]
    if not base_url:
        return jsonify({"error": "Base URL required"}), 400

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except:
        cfg = {"llm": {}, "tools": {"mouse_path": "agent/tools.mouse.json", "keyboard_path": "agent/tools.keyboard.json", "enable_mouse": True, "enable_keyboard": True}, "automation": {"delay_ms": 150, "timeout": 8000}, "security": {"op_whitelist": ["screen", "input"]}}

    cfg["llm"]["api_key"] = api_key
    cfg["llm"]["base_url"] = base_url
    cfg["llm"]["model"] = model
    cfg["llm"]["temperature"] = cfg["llm"].get("temperature", 0.2)

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

    global _cfg
    _cfg = None
    ensure_loaded()

    return jsonify({"ok": True})

@app.route("/")
def store():
    return render_template("store.html", plugins=PLUGINS, configured=config_complete())

@app.route("/setup")
def setup_page():
    return render_template("setup.html", providers=API_PROVIDERS)

@app.route("/wgui")
def wgui():
    if not config_complete():
        return redirect("/setup")
    return render_template("wgui.html")

@app.route("/api/screenshot")
def api_screenshot():
    b64 = engine.capture_screen_base64(scale=0.5, fmt="JPEG", quality=70)
    return jsonify({"image": b64})

@app.route("/api/send", methods=["POST"])
def api_send():
    if not ensure_loaded():
        return jsonify({"error": "Not configured"}), 400

    data = request.get_json()
    task = data.get("task", "").strip()
    if not task:
        return jsonify({"error": "empty task"}), 400

    with _msg_lock:
        b64 = engine.capture_screen_base64(scale=1.0, fmt="PNG")
        _messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": task},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ]
        })

        try:
            resp = _client.chat.completions.create(
                model=_llm_cfg["model"],
                messages=_messages,
                temperature=_llm_cfg.get("temperature", 0.2),
            )
            content = resp.choices[0].message.content
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        _messages.append({"role": "assistant", "content": content})

        for line in content.split("\n"):
            line = line.strip()
            if line:
                engine.execute_command(line, _mouse_names, _keyboard_names, _mouse_commands, _tools_cfg)

        b64_after = engine.capture_screen_base64(scale=1.0, fmt="PNG")

        if "FINISHED" not in content:
            _messages.append({
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
