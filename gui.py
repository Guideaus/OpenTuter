import json
import sys
import time
from openai import OpenAI
import ugui.oobe as oobe
import core as engine

def setup():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    llm = cfg["llm"]
    if any(not llm.get(field, "").strip() for field in ["api_key", "base_url", "model"]):
        oobe.main()
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        llm = cfg["llm"]
    if not llm.get("api_key", "").strip():
        base = llm.get("base_url", "")
        is_local = any(h in base for h in ("localhost", "127.0.0.1"))
        if is_local:
            llm["api_key"] = "not-needed"
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4, ensure_ascii=False)
        else:
            print("API key is required for remote providers. Run OOBE setup again.")
            sys.exit(1)
    return cfg

def call_llm(messages, client, llm_cfg):
    return client.chat.completions.create(
        model=llm_cfg["model"],
        messages=messages,
        temperature=llm_cfg.get("temperature", 0.2),
    ).choices[0].message.content

def main():
    cfg = setup()
    llm_cfg = cfg["llm"]
    tools_cfg = cfg["tools"]

    abort = engine.AbortController()
    abort.start()

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
    print("OpenTuter ready. Type your task (or 'exit' to quit).")
    print("Press DEL 3 times quickly to abort any operation.\n")

    while True:
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in ("exit", "quit", "q"):
            break

        abort.aborted = False
        b64 = engine.capture_screen_base64()
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_input},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ]
        })

        while not abort.aborted:
            try:
                content = call_llm(messages, client, llm_cfg)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                break
            print(f"\n{content}\n")
            messages.append({"role": "assistant", "content": content})

            if "FINISHED" in content:
                break

            for line in content.split("\n"):
                if abort.aborted:
                    break
                line = line.strip()
                if line:
                    engine.execute_command(line, mouse_names, keyboard_names, mouse_commands, tools_cfg)

            if abort.aborted:
                break

            time.sleep(0.3)
            b64 = engine.capture_screen_base64()
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Commands executed. Updated screen below. Continue or output FINISHED if done."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]
            })

        if abort.aborted:
            print("[Operation aborted by user - triple DEL detected]")
            abort.aborted = False

if __name__ == "__main__":
    main()
