from simtest.cli import app
import sys

print("✅ [__main__.py] __main__ path =", __file__)

if __name__ == "__main__":
    print("✅ [__main__.py] Running app() with args:", sys.argv)
    app(prog_name="simtest")
