"""Start Novi. Used by run.bat and run.sh; `python app/run.py --help` lists the flags."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from novi.server import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
