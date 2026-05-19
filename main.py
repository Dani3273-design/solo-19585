import sys
from game.ui import GomokuUI


def main():
    ui = GomokuUI()
    try:
        ui.run()
    except KeyboardInterrupt:
        print("\n游戏已退出")
        sys.exit(0)


if __name__ == "__main__":
    main()
