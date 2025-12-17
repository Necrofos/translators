"""
Интерфейс командной строки для Expression Interpreter
"""

import argparse
from parser_core import run_source


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Expression Interpreter - вычисление выражений со сложением и сравнением',
        epilog="""
Примеры:
  python3 cli.py                     # Интерактивный режим
  python3 cli.py -e "2+3 < 4"       # Одно выражение
  python3 cli.py input.txt          # Выражения из файла
        """
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        help='Файл с выражениями'
    )
    
    parser.add_argument(
        '-e', '--expression',
        help='Вычислить одно выражение'
    )
    
    return parser.parse_args()


def run_prompt():
    """Интерактивный режим"""
    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            
            result = run_source(line)
            if result is not None:
                print(result)
        
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break


def run_file(filename: str):
    """Чтение из файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                result = run_source(line)
                if result is not None:
                    print(result)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
    except IOError as e:
        print(f"Error reading file: {e}")


def main():
    """Главная функция CLI"""
    args = parse_arguments()
    
    if args.expression:
        result = run_source(args.expression)
        if result is not None:
            print(result)
    elif args.file:
        run_file(args.file)
    else:
        run_prompt()


if __name__ == "__main__":
    main()