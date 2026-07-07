import sys
import gui

if __name__ in {"__main__", "__mp_main__"}:
    if len(sys.argv) > 1 and sys.argv[1] == "extension":
        from extension.server import main as server_main
        server_main()
    else:
        gui.main()
