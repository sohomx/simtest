import os
from simtest.cli import app
import sys

print("✅ [__main__.py] __main__ path =", __file__)

if __name__ == "__main__":
    print("✅ [__main__.py] Running app() with args:", sys.argv)
    app(prog_name="simtest")

@app.command()
def ci():
    """Run all curated test packs in CI mode."""
    os.system("poetry run simtest fuzz --suite policy-violation --quick")
    os.system("poetry run simtest fuzz --suite long-context --quick")
