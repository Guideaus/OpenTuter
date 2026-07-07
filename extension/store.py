from nicegui import ui

PLUGINS = [
    {
        "name": "wgui",
        "title": "Web GUI",
        "description": "A web-based control panel for OpenTuter. Chat with the AI, see the live screen, and control your desktop from a browser.",
        "author": "OpenTuter",
        "version": "1.0.0",
    },
]

_content = None

def create_ui():
    global _content
    _content = ui.column().classes("w-full")
    show_store()

def show_store():
    _content.clear()
    with _content:
        with ui.column().classes("w-full max-w-3xl mx-auto p-6 gap-6"):
            ui.label("Available Plugins").classes("text-h6")
            for plugin in PLUGINS:
                with ui.card().classes("w-full"):
                    with ui.row().classes("items-start justify-between w-full"):
                        with ui.column().classes("gap-1"):
                            ui.label(plugin["title"]).classes("text-h6")
                            ui.label(f"by {plugin['author']}  v{plugin['version']}").classes(
                                "text-caption text-grey-6"
                            )
                            ui.label(plugin["description"]).classes("text-body2 text-grey-8")
                        ui.button("Open", on_click=lambda p=plugin: launch(p["name"])).props(
                            "flat color=primary"
                        )

def launch(name):
    _content.clear()
    with _content:
        ui.button("← Back to Store", on_click=show_store).props("flat")
        if name == "wgui":
            from extension.wgui import main as wgui
            wgui.create_ui()
