from simtest.cli import init
import sys
import typer

print("✅ [__main__.py] __main__ path =", __file__)

if __name__ == "__main__":
    print("✅ [__main__.py] Running init() with args:", sys.argv)
    typer.run(init)
