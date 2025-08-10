import os
from datetime import datetime


DEBUG_ANALYZER: bool = True
# DEBUG_ANALYZER: bool = False
def debug(msg: str) -> None:
    if DEBUG_ANALYZER:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fname = os.path.basename(__file__)
        print(f"[{now} {fname}] {msg}")