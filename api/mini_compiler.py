# mini_compiler.py
# Simple Mini Compiler:
# 1) Lexical Analysis
# 2) Syntax Analysis
# 3) Semantic Analysis
# 4) Three Address Code Generation

KEYWORDS = {"int", "print"}
OPERATORS = {"+", "-", "*", "/", "="}
SYMBOLS = {";", "(", ")"}


class Token:
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"


# -----------------------------
# 1. Lexical Analysis
# -----------------------------
def lexer(source_code):
    tokens = []
    i = 0

    while i < len(source_code):
        char = source_code[i]

        if char.isspace():
            i += 1
            continue

        if char.isalpha():
            word = ""
            while i < len(source_code) and source_code[i].isalnum():
                word += source_code[i]
                i += 1

            if word in KEYWORDS:
                tokens.append(Token("KEYWORD", word))
            else:
                tokens.append(Token("IDENTIFIER", word))
            continue

        if char.isdigit():
            number = ""
            while i < len(source_code) and source_code[i].isdigit():
                number += source_code[i]
                i += 1
            tokens.append(Token("NUMBER", number))
            continue

        if char in OPERATORS:
            tokens.append(Token("OPERATOR", char))
            i += 1
            continue

        if char in SYMBOLS:
            tokens.append(Token("SYMBOL", char))
            i += 1
            continue

        raise Exception(f"Unknown character: {char}")

    return tokens


# -----------------------------
# 2. Syntax Analysis
# -----------------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def match(self, token_type, value=None):
        token = self.current_token()

        if token is None:
            raise Exception("Unexpected end of code")

        if token.type != token_type:
            raise Exception(f"Expected {token_type}, got {token.type}")

        if value is not None and token.value != value:
            raise Exception(f"Expected '{value}', got '{token.value}'")

        self.pos += 1
        return token

    def parse(self):
        statements = []

        while self.current_token() is not None:
            statements.append(self.parse_statement())

        return statements

    def parse_statement(self):
        token = self.current_token()

        if token.type == "KEYWORD" and token.value == "int":
            return self.parse_declaration()

        if token.type == "KEYWORD" and token.value == "print":
            return self.parse_print()

        raise Exception(f"Invalid statement starting with: {token.value}")

    def parse_declaration(self):
        self.match("KEYWORD", "int")
        var_name = self.match("IDENTIFIER").value
        self.match("OPERATOR", "=")
        expression = self.parse_expression()
        self.match("SYMBOL", ";")

        return {
            "type": "declaration",
            "name": var_name,
            "expression": expression
        }

    def parse_print(self):
        self.match("KEYWORD", "print")
        self.match("SYMBOL", "(")
        var_name = self.match("IDENTIFIER").value
        self.match("SYMBOL", ")")
        self.match("SYMBOL", ";")

        return {
            "type": "print",
            "name": var_name
        }

    def parse_expression(self):
        left = self.parse_term()

        while self.current_token() is not None:
            token = self.current_token()

            if token.type == "OPERATOR" and token.value in {"+", "-", "*", "/"}:
                operator = self.match("OPERATOR").value
                right = self.parse_term()

                left = {
                    "type": "binary_expression",
                    "operator": operator,
                    "left": left,
                    "right": right
                }
            else:
                break

        return left

    def parse_term(self):
        token = self.current_token()

        if token.type == "NUMBER":
            value = self.match("NUMBER").value
            return {
                "type": "number",
                "value": value
            }

        if token.type == "IDENTIFIER":
            name = self.match("IDENTIFIER").value
            return {
                "type": "identifier",
                "name": name
            }

        raise Exception(f"Invalid expression term: {token.value}")


# -----------------------------
# 3. Semantic Analysis
# -----------------------------
def semantic_analysis(ast):
    declared_variables = set()
    errors = []

    def check_expression(expression):
        if expression["type"] == "identifier":
            if expression["name"] not in declared_variables:
                errors.append(f"Undeclared variable: {expression['name']}")

        elif expression["type"] == "binary_expression":
            check_expression(expression["left"])
            check_expression(expression["right"])

    for statement in ast:
        if statement["type"] == "declaration":
            var_name = statement["name"]

            if var_name in declared_variables:
                errors.append(f"Duplicate variable declaration: {var_name}")
            else:
                check_expression(statement["expression"])
                declared_variables.add(var_name)

        elif statement["type"] == "print":
            if statement["name"] not in declared_variables:
                errors.append(f"Undeclared variable: {statement['name']}")

    return errors


# -----------------------------
# 4. Intermediate Code Generation
# -----------------------------
class CodeGenerator:
    def __init__(self):
        self.temp_count = 0
        self.code = []

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate_expression(self, expression):
        if expression["type"] == "number":
            return expression["value"]

        if expression["type"] == "identifier":
            return expression["name"]

        if expression["type"] == "binary_expression":
            left = self.generate_expression(expression["left"])
            right = self.generate_expression(expression["right"])
            temp = self.new_temp()

            self.code.append(
                f"{temp} = {left} {expression['operator']} {right}"
            )

            return temp

    def generate(self, ast):
        for statement in ast:
            if statement["type"] == "declaration":
                result = self.generate_expression(statement["expression"])
                self.code.append(f"{statement['name']} = {result}")

            elif statement["type"] == "print":
                self.code.append(f"print {statement['name']}")

        return self.code


# -----------------------------
# Helper Function
# -----------------------------
def print_syntax_tree(ast):
    for statement in ast:
        print(statement)


def run_compiler(source_code):
    print("=" * 50)
    print("SOURCE CODE:")
    print(source_code)

    try:
        print("\nTOKENS:")
        tokens = lexer(source_code)
        for token in tokens:
            print(token)

        print("\nSYNTAX TREE:")
        parser = Parser(tokens)
        ast = parser.parse()
        print_syntax_tree(ast)

        print("\nSEMANTIC CHECK:")
        errors = semantic_analysis(ast)

        if errors:
            for error in errors:
                print("Error:", error)
            return

        print("No errors")

        print("\nTHREE ADDRESS CODE:")
        generator = CodeGenerator()
        tac = generator.generate(ast)

        for line in tac:
            print(line)

    except Exception as e:
        print("Compiler Error:", e)


