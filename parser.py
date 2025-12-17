"""
Транслятор для выражений со сложением и операциями сравнения над целыми числами.
Пример: 2+3 < 4
"""

# Грамматика:
# Expression   ::= AddExpr (ComparisonOp AddExpr)*
# AddExpr      ::= Term (('+' | '-') Term)*
# Term         ::= NUMBER | '(' Expression ')'
# ComparisonOp ::= '<' | '>' | '=' | '!='
# NUMBER       ::= [0-9]+

from enum import Enum
from typing import List, Optional, Union


# =============================================
# Часть 1: Сканер (Лексический анализатор)
# =============================================

class TokenType(Enum):
    """Типы токенов"""
    NUMBER = 'NUMBER'
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    LESS = 'LESS'
    GREATER = 'GREATER'
    EQUAL = 'EQUAL'
    NOT_EQUAL = 'NOT_EQUAL'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    EOF = 'EOF'


class Token:
    """Класс для представления токена"""
    def __init__(self, type: TokenType, value: str = '', line: int = 1, column: int = 1):
        self.type = type
        self.value = value
        self.line = line
        self.column = column


class ScannerError(Exception):
    """Исключение для ошибок сканера"""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f'Line {line}, Column {column}: {message}')


class Scanner:
    """Лексический анализатор"""
    
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_column = 1
    
    def scan_tokens(self) -> List[Token]:
        """Сканирование всех токенов из исходного текста"""
        while not self.is_at_end():
            self.start = self.current
            self.start_column = self.column
            self.scan_token()
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens
    
    def scan_token(self):
        """Сканирование одного токена"""
        char = self.advance()
        
        if char in ' \t\r':
            return
        
        if char == '\n':
            self.line += 1
            self.column = 1
            return
        
        if char.isdigit():
            self.number()
            return
        
        if char == '+':
            self.add_token(TokenType.PLUS, '+')
        elif char == '-':
            self.add_token(TokenType.MINUS, '-')
        elif char == '<':
            self.add_token(TokenType.LESS, '<')
        elif char == '>':
            self.add_token(TokenType.GREATER, '>')
        elif char == '(':
            self.add_token(TokenType.LPAREN, '(')
        elif char == ')':
            self.add_token(TokenType.RPAREN, ')')
        elif char == '=':
            if self.match('='):
                self.add_token(TokenType.EQUAL, '==')
            else:
                self.error(f"Unexpected character '{char}'")
        elif char == '!':
            if self.match('='):
                self.add_token(TokenType.NOT_EQUAL, '!=')
            else:
                self.error(f"Unexpected character '{char}'")
        else:
            self.error(f"Unexpected character '{char}'")
    
    def number(self):
        """Чтение числа"""
        while self.peek().isdigit():
            self.advance()
        
        next_char = self.peek()
        if next_char.isalpha() or next_char == '_':
            self.error("Invalid number format")
        
        value = self.source[self.start:self.current]
        self.add_token(TokenType.NUMBER, value)
    
    def match(self, expected: str) -> bool:
        """Проверяет соответствие следующего символа ожидаемому"""
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True
    
    def peek(self) -> str:
        """Возвращает текущий символ без продвижения вперед"""
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
    
    def advance(self) -> str:
        """Возвращает текущий символ и продвигается вперед"""
        if self.is_at_end():
            return '\0'
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char
    
    def is_at_end(self) -> bool:
        """Проверяет, достигнут ли конец исходного текста"""
        return self.current >= len(self.source)
    
    def add_token(self, token_type: TokenType, value: str = ''):
        """Добавляет токен в список"""
        self.tokens.append(Token(token_type, value, self.line, self.start_column))
    
    def error(self, message: str):
        """Генерирует ошибку сканера"""
        raise ScannerError(message, self.line, self.start_column)


# =============================================
# Часть 2: Парсер (Синтаксический анализатор)
# =============================================

class ParserError(Exception):
    """Исключение для ошибок парсера"""
    def __init__(self, message: str, token: Token):
        super().__init__(f'Line {token.line}, Column {token.column}: {message}')


class ASTNode:
    """Базовый класс для узлов AST"""
    def __init__(self, token: Token = None):
        self.token = token


class NumberNode(ASTNode):
    """Узел для чисел"""
    def __init__(self, token: Token):
        super().__init__(token)
        self.value = int(token.value)


class BinaryOpNode(ASTNode):
    """Узел для бинарных операций"""
    def __init__(self, left: ASTNode, op: Token, right: ASTNode):
        super().__init__(op)
        self.left = left
        self.op = op
        self.right = right


class Parser:
    """Рекурсивный нисходящий предикативный парсер"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
    
    def parse(self) -> ASTNode:
        """Начало разбора - выражение"""
        return self.expression()
    
    def expression(self) -> ASTNode:
        """Expression ::= AddExpr (ComparisonOp AddExpr)*"""
        node = self.add_expr()
        
        while self.is_comparison_op():
            op = self.advance()
            right = self.add_expr()
            node = BinaryOpNode(node, op, right)
        
        return node
    
    def add_expr(self) -> ASTNode:
        """AddExpr ::= Term (('+' | '-') Term)*"""
        node = self.term()
        
        while self.match(TokenType.PLUS) or self.match(TokenType.MINUS):
            op = self.previous()
            right = self.term()
            node = BinaryOpNode(node, op, right)
        
        return node
    
    def term(self) -> ASTNode:
        """Term ::= NUMBER | '(' Expression ')'"""
        if self.match(TokenType.NUMBER):
            return NumberNode(self.previous())
        
        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        
        self.error("Expected number or '('")
    
    def is_comparison_op(self) -> bool:
        """Проверяет, является ли текущий токен оператором сравнения"""
        token = self.peek()
        return token.type in [TokenType.LESS, TokenType.GREATER, 
                             TokenType.EQUAL, TokenType.NOT_EQUAL]
    
    def match(self, token_type: TokenType) -> bool:
        """Проверяет соответствие текущего токена ожидаемому типу"""
        if self.is_at_end():
            return False
        
        if self.peek().type == token_type:
            self.advance()
            return True
        return False
    
    def consume(self, token_type: TokenType, message: str) -> Token:
        """Потребляет токен ожидаемого типа или генерирует ошибку"""
        if self.check(token_type):
            return self.advance()
        
        raise ParserError(message, self.peek())
    
    def check(self, token_type: TokenType) -> bool:
        """Проверяет тип текущего токена без потребления"""
        if self.is_at_end():
            return False
        return self.peek().type == token_type
    
    def advance(self) -> Token:
        """Перемещается к следующему токену"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()
    
    def previous(self) -> Token:
        """Возвращает предыдущий токен"""
        return self.tokens[self.current - 1]
    
    def peek(self) -> Token:
        """Возвращает текущий токен без потребления"""
        return self.tokens[self.current]
    
    def is_at_end(self) -> bool:
        """Проверяет, достигнут ли конец потока токенов"""
        return self.peek().type == TokenType.EOF
    
    def error(self, message: str):
        """Генерирует ошибку парсера"""
        raise ParserError(message, self.peek())


# =============================================
# Часть 3: Семантический анализатор/Интерпретатор
# =============================================

class InterpreterError(Exception):
    """Исключение для ошибок интерпретатора"""
    def __init__(self, message: str, node: ASTNode = None):
        if node and node.token:
            super().__init__(f'Line {node.token.line}, Column {node.token.column}: {message}')
        else:
            super().__init__(message)


class Interpreter:
    """Семантический анализатор и интерпретатор"""
    
    def __init__(self):
        pass
    
    def interpret(self, node: ASTNode) -> Union[int, bool]:
        """Интерпретация AST-дерева"""
        if isinstance(node, NumberNode):
            return self.visit_number(node)
        elif isinstance(node, BinaryOpNode):
            return self.visit_binary_op(node)
        else:
            raise InterpreterError(f"Unknown node type: {type(node)}", node)
    
    def visit_number(self, node: NumberNode) -> int:
        """Обработка узла числа"""
        return node.value
    
    def visit_binary_op(self, node: BinaryOpNode) -> Union[int, bool]:
        """Обработка узла бинарной операции"""
        left = self.interpret(node.left)
        right = self.interpret(node.right)
        
        op_type = node.op.type
        
        if op_type == TokenType.PLUS:
            if not isinstance(left, int) or not isinstance(right, int):
                raise InterpreterError("Operands for '+' must be integers", node)
            return left + right
        
        elif op_type == TokenType.MINUS:
            if not isinstance(left, int) or not isinstance(right, int):
                raise InterpreterError("Operands for '-' must be integers", node)
            return left - right
        
        elif op_type == TokenType.LESS:
            return left < right
        
        elif op_type == TokenType.GREATER:
            return left > right
        
        elif op_type == TokenType.EQUAL:
            return left == right
        
        elif op_type == TokenType.NOT_EQUAL:
            return left != right
        
        else:
            raise InterpreterError(f"Unknown operator: {node.op.value}", node)


# =============================================
# Главная функция обработки
# =============================================

def run_source(source: str) -> Optional[Union[int, bool]]:
    """Обрабатывает исходный код и возвращает результат"""
    try:
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        interpreter = Interpreter()
        return interpreter.interpret(ast)
    
    except ScannerError as e:
        print(f"Scanner Error: {e}")
    except ParserError as e:
        print(f"Parser Error: {e}")
    except InterpreterError as e:
        print(f"Interpreter Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    
    return None