KEYWORDS = {"print"}
OPERATORS = {"+", "-", "*", "/", "="}
SYMBOLS = {"(", ")", ";"}


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

        # تجاهل التعليقات (#)
        if char == "#":
            while i < len(source_code) and source_code[i] != "\n":
                i += 1
            continue

        # تجاهل الـ Docstrings
        if source_code[i:i+3] in ('"""', "'''"):
            quote = source_code[i:i+3]
            i += 3
            while i < len(source_code) and source_code[i:i+3] != quote:
                i += 1
            i += 3
            continue

        # النصوص (Strings)
        if char in ('"', "'"):
            quote = char
            i += 1
            string_val = ""
            while i < len(source_code) and source_code[i] != quote:
                string_val += source_code[i]
                i += 1
            if i >= len(source_code):
                raise Exception("Unterminated string literal")
            i += 1
            tokens.append(Token("STRING", string_val))
            continue

        # المعرفات والكلمات المفتاحية
        if char.isalpha() or char == "_":
            word = ""
            while i < len(source_code) and (source_code[i].isalnum() or source_code[i] == "_"):
                word += source_code[i]
                i += 1

            if word in KEYWORDS:
                tokens.append(Token("KEYWORD", word))
            else:
                tokens.append(Token("IDENTIFIER", word))
            continue

        # الأرقام
        if char.isdigit():
            number = ""
            while i < len(source_code) and source_code[i].isdigit():
                number += source_code[i]
                i += 1
            tokens.append(Token("NUMBER", number))
            continue

        # المعاملات الرياضية
        if char in OPERATORS:
            tokens.append(Token("OPERATOR", char))
            i += 1
            continue

        # الرموز
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
            if self.current_token() and self.current_token().type == "SYMBOL" and self.current_token().value == ";":
                self.match("SYMBOL", ";")
        return statements

    def parse_statement(self):
        token = self.current_token()

        if token.type == "KEYWORD" and token.value == "print":
            return self.parse_print()

        if token.type == "IDENTIFIER":
            return self.parse_assignment()

        raise Exception(f"Invalid statement starting with: {token.value}")

    def parse_assignment(self):
        var_name = self.match("IDENTIFIER").value
        self.match("OPERATOR", "=")
        expression = self.parse_expression()
        return {
            "type": "declaration",
            "name": var_name,
            "expression": expression
        }

    def parse_print(self):
        self.match("KEYWORD", "print")
        self.match("SYMBOL", "(")
        
        arg_token = self.current_token()
        if arg_token.type in ("IDENTIFIER", "STRING", "NUMBER"):
            self.pos += 1
            arg = {"type": arg_token.type.lower(), "value": arg_token.value}
        else:
            raise Exception(f"Invalid argument inside print: {arg_token.value}")

        self.match("SYMBOL", ")")
        return {
            "type": "print",
            "argument": arg
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
            val = self.match("NUMBER").value
            return {"type": "number", "value": val}

        if token.type == "STRING":
            val = self.match("STRING").value
            return {"type": "string", "value": f'"{val}"'}

        if token.type == "IDENTIFIER":
            name = self.match("IDENTIFIER").value
            return {"type": "identifier", "name": name}

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
                errors.append(f"NameError: name '{expression['name']}' is not defined")
        elif expression["type"] == "binary_expression":
            check_expression(expression["left"])
            check_expression(expression["right"])

    for statement in ast:
        if statement["type"] == "declaration":
            check_expression(statement["expression"])
            declared_variables.add(statement["name"])

        elif statement["type"] == "print":
            arg = statement["argument"]
            if arg["type"] == "identifier" and arg["value"] not in declared_variables:
                errors.append(f"NameError: name '{arg['value']}' is not defined")

    return errors


# -----------------------------
# 4. Three Address Code (TAC)
# -----------------------------
class CodeGenerator:
    def __init__(self):
        self.temp_count = 0
        self.code = []

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate_expression(self, expression):
        if expression["type"] in ("number", "string"):
            return expression["value"]

        if expression["type"] == "identifier":
            return expression["name"]

        if expression["type"] == "binary_expression":
            left = self.generate_expression(expression["left"])
            right = self.generate_expression(expression["right"])
            temp = self.new_temp()
            self.code.append(f"{temp} = {left} {expression['operator']} {right}")
            return temp

    def generate(self, ast):
        for statement in ast:
            if statement["type"] == "declaration":
                result = self.generate_expression(statement["expression"])
                self.code.append(f"{statement['name']} = {result}")

            elif statement["type"] == "print":
                val = statement["argument"]["value"]
                self.code.append(f"print {val}")

        return self.code


# -----------------------------
# 5. Virtual Machine / Execution (Output Generator)
# -----------------------------
class TACInterpreter:
    def __init__(self, tac_instructions):
        self.tac = tac_instructions
        self.env = {}
        self.stdout = []

    def run(self):
        for line in self.tac:
            line = line.strip()
            if not line:
                continue

            # أوامر الطباعة: print x
            if line.startswith("print "):
                target = line.replace("print ", "").strip()
                val = self._resolve_val(target)
                self.stdout.append(str(val))

            # أوامر الإسناد والحساب: var = a + b أو var = val
            elif "=" in line:
                left, right = [part.strip() for part in line.split("=", 1)]
                parts = right.split()

                if len(parts) == 1:
                    self.env[left] = self._resolve_val(parts[0])
                elif len(parts) == 3:
                    op1 = self._resolve_val(parts[0])
                    op = parts[1]
                    op2 = self._resolve_val(parts[2])
                    self.env[left] = self._eval_op(op1, op, op2)

        return self.stdout

    def _resolve_val(self, token):
        # نصوص
        if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            return token[1:-1]
        # أرقام
        if token.isdigit():
            return int(token)
        # متغيرات سابقة في الذاكرة
        if token in self.env:
            return self.env[token]
        return token

    def _eval_op(self, left, op, right):
        try:
            if op == "+": return left + right
            if op == "-": return left - right
            if op == "*": return left * right
            if op == "/": return left // right if isinstance(left, int) and isinstance(right, int) else left / right
        except Exception:
            return 0
        return 0