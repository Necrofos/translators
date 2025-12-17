"""
Expression Interpreter - точка входа в программу
"""

import sys
from cli import main as cli_main


def main():
    """Точка входа в приложение"""
    # Просто передаем управление в CLI
    cli_main()


if __name__ == "__main__":
    main()