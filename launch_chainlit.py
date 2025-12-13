import sys
import os
import argparse
import uvicorn.logging
from chainlit.cli import cli

# Monkeypatch uvicorn's formatters to avoid sys.stdout.isatty() check
# This fixes the "AttributeError: 'Tee' object has no attribute 'isatty'" error
# by forcing colors to be disabled for both DefaultFormatter and AccessFormatter.

original_default_init = uvicorn.logging.DefaultFormatter.__init__
def patched_default_init(self, fmt=None, datefmt=None, style="%", use_colors=None):
    return original_default_init(self, fmt=fmt, datefmt=datefmt, style=style, use_colors=False)

uvicorn.logging.DefaultFormatter.__init__ = patched_default_init

original_access_init = uvicorn.logging.AccessFormatter.__init__
def patched_access_init(self, fmt=None, datefmt=None, style="%", use_colors=None):
    return original_access_init(self, fmt=fmt, datefmt=datefmt, style=style, use_colors=False)

uvicorn.logging.AccessFormatter.__init__ = patched_access_init

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--adventure-guide",
        type=str,
        default="./data/Lost Mine of Phandelver.md",
    )
    parser.add_argument(
        "--knowledge-graph",
        type=str,
        default="./dnd_system/state/knowledge_graph_template.json",
    )

    args, _unknown = parser.parse_known_args(sys.argv[1:])

    os.environ["AGENTICDM_ADVENTURE_GUIDE_PATH"] = args.adventure_guide
    os.environ["AGENTICDM_KNOWLEDGE_GRAPH_TEMPLATE_PATH"] = args.knowledge_graph_template

    # Ensure the script acts like 'chainlit run dnd_system/app.py'
    sys.argv = ["chainlit", "run", "dnd_system/app.py"]
    try:
        cli()
    except SystemExit:
        pass
