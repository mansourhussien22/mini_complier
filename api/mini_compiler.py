KEYWORDS = {"print", "True", "False", "None"}
OPERATORS = {
    "+", "-", "*", "/", "=", "+=", "-=", "*=", "/=", "**", "//",
    "&", "|", "^", "~", "%", "@"
}
SYMBOLS = {"(", ")", ";", ",", "$", "#"}


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
    n = len(source_code)

    while i < n:
        char = source_code[i]

        if char.isspace(): 
            i += 1
            continue

        # التعامل مع # كرمز خاص أو كتعليق حسب السياق
        # إذا تبعه مسافة أو نص بدون معامل، يعتبر تعليقاً يتم تخطيه
        if char == "#" and (i + 1 < n and source_code[i+1].isalpha()):
            tokens.append(Token("SPECIAL", "#"))
            i += 1
            continue
        elif char == "#":
            while i < n and source_code[i] != "\n":
                i += 1
            continue

        # تجاهل الـ Docstrings
        if source_code[i:i+3] in ('"""', "'''"):
            quote = source_code[i:i+3]
            i += 3
            while i < n and source_code[i:i+3] != quote:
                i += 1
            i += 3
            continue

        # المعاملات المركبة الثنائية
        two_char = source_code[i:i+2]
        if two_char in {"+=", "-=", "*=", "/=", "**", "//", "&=", "|="}:
            tokens.append(Token("OPERATOR", two_char))
            i += 2
            continue

        # النصوص
        if char in ('"', "'"):
            quote = char
            i += 1
            string_val = ""
            while i < n and source_code[i] != quote:
                string_val += source_code[i]
                i += 1
            if i >= n:
                raise Exception("Unterminated string literal")
            i += 1
            tokens.append(Token("STRING", string_val))
            continue

        # دعم $ مع الحروف والشرطة السفلية في أسماء المتغيرات
        if char.isalpha() or char in {"_", "$"}:
            word = ""
            while i < n and (source_code[i].isalnum() or source_code[i] in {"_", "$"}):
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
            has_dot = False
            while i < n and (source_code[i].isdigit() or source_code[i] == "."):
                if source_code[i] == ".":
                    if has_dot:
                        break
                    has_dot = True
                number += source_code[i]
                i += 1
            tokens.append(Token("NUMBER", number))
            continue

        # المعاملات الأحادية والرموز الخاصة (&, |, ^, ~, %, @)
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
        op_token = self.match("OPERATOR").value
        expression = self.parse_expression()

        if op_token != "=":
            base_op = op_token[0]
            expression = {
                "type": "binary_expression",
                "operator": base_op,
                "left": {"type": "identifier", "name": var_name},
                "right": expression
            }

        return {
            "type": "declaration",
            "name": var_name,
            "expression": expression
        }

    def parse_print(self):
        self.match("KEYWORD", "print")
        self.match("SYMBOL", "(")
        args = []
        if self.current_token() and not (self.current_token().type == "SYMBOL" and self.current_token().value == ")"):
            args.append(self.parse_expression())
            while self.current_token() and self.current_token().type == "SYMBOL" and self.current_token().value == ",":
                self.match("SYMBOL", ",")
                args.append(self.parse_expression())

        self.match("SYMBOL", ")")
        return {"type": "print", "arguments": args}

    def parse_expression(self):
        left = self.parse_term()
        # دعم العمليات الحسابية وعمليات البت الخاصة (&, |, ^, %, //, **)
        valid_ops = {"+", "-", "*", "/", "**", "//", "&", "|", "^", "%"}
        while self.current_token() is not None:
            token = self.current_token()
            if token.type == "OPERATOR" and token.value in valid_ops:
                op = self.match("OPERATOR").value
                right = self.parse_term()
                left = {
                    "type": "binary_expression",
                    "operator": op,
                    "left": left,
                    "right": right
                }
            else:
                break
        return left

    def parse_term(self):
        token = self.current_token()

        # دعم الـ Unary Operator (مثل ~ للأعداد الثنائية)
        if token.type == "OPERATOR" and token.value == "~":
            self.match("OPERATOR", "~")
            term = self.parse_term()
            return {"type": "unary_expression", "operator": "~", "operand": term}

        if token.type == "SYMBOL" and token.value == "(":
            self.match("SYMBOL", "(")
            expr = self.parse_expression()
            self.match("SYMBOL", ")")
            return expr

        if token.type == "NUMBER":
            return {"type": "number", "value": self.match("NUMBER").value}

        if token.type == "STRING":
            return {"type": "string", "value": f'"{self.match("STRING").value}"'}

        if token.type == "KEYWORD" and token.value in {"True", "False", "None"}:
            return {"type": "literal", "value": self.match("KEYWORD").value}

        if token.type == "IDENTIFIER":
            return {"type": "identifier", "name": self.match("IDENTIFIER").value}

        raise Exception(f"Invalid expression term: {token.value}")


# -----------------------------
# 3. Semantic Analysis
# -----------------------------
def semantic_analysis(ast):
    declared_variables = set()
    errors = []

    def check_expression(expression):
        if not isinstance(expression, dict):
            return
        if expression["type"] == "identifier":
            if expression["name"] not in declared_variables:
                errors.append(f"NameError: name '{expression['name']}' is not defined")
        elif expression["type"] == "binary_expression":
            check_expression(expression["left"])
            check_expression(expression["right"])
        elif expression["type"] == "unary_expression":
            check_expression(expression["operand"])

    for statement in ast:
        if statement["type"] == "declaration":
            check_expression(statement["expression"])
            declared_variables.add(statement["name"])
        elif statement["type"] == "print":
            for arg in statement["arguments"]:
                check_expression(arg)

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
        if expression["type"] in ("number", "string", "literal"):
            return expression["value"]

        if expression["type"] == "identifier":
            return expression["name"]

        if expression["type"] == "unary_expression":
            operand = self.generate_expression(expression["operand"])
            temp = self.new_temp()
            self.code.append(f"{temp} = {expression['operator']}{operand}")
            return temp

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
                args = [self.generate_expression(arg) for arg in statement["arguments"]]
                self.code.append(f"print {', '.join(args)}")

        return self.code


# -----------------------------
# 5. Virtual Machine / Interpreter
# -----------------------------
import re

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

            # 1. أوامر الطباعة: print ...
            if line.startswith("print "):
                content = line[6:].strip()
                args = self._split_args(content)
                resolved = [str(self._resolve_val(arg.strip())) for arg in args]
                self.stdout.append(" ".join(resolved))

            # 2. أوامر الإسناد: var = value
            elif "=" in line:
                left, right = [part.strip() for part in line.split("=", 1)]
                
                # فحص النصوص الصريحة ذات المسافات
                if (right.startswith('"') and right.endswith('"')) or (right.startswith("'") and right.endswith("'")):
                    self.env[left] = right[1:-1]
                else:
                    parts = right.split()
                    if len(parts) == 1:
                        if parts[0].startswith("~"):
                            val = self._resolve_val(parts[0][1:])
                            self.env[left] = ~int(val)
                        else:
                            self.env[left] = self._resolve_val(parts[0])
                    elif len(parts) == 3:
                        op1 = self._resolve_val(parts[0])
                        op = parts[1]
                        op2 = self._resolve_val(parts[2])
                        self.env[left] = self._eval_op(op1, op, op2)

        return self.stdout

    def _split_args(self, text):
        """تقسيم وسائط print مع الحفاظ على النصوص والمسافات"""
        pattern = r',\s*(?=(?:[^\'"]*[\'"][^\'"]*[\'"])*[^\'"]*$)'
        return re.split(pattern, text)

    def _resolve_val(self, token):
        token = token.strip()
        # نصوص مباشرة
        if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            return token[1:-1]
        
        # ثوابت منطقية وقيمة فارغة
        if token == "True": return True
        if token == "False": return False
        if token == "None": return None
        
        # أرقام
        if token.replace(".", "", 1).isdigit():
            return float(token) if "." in token else int(token)
            
        # جلب القيمة من الذاكرة إذا كان متغيراً مسجلاً
        if token in self.env:
            return self.env[token]
            
        # رمي Error فوري بدلاً من طباعة اسم المتغير كنص
        raise Exception(f"NameError: name '{token}' is not defined")

    def _eval_op(self, left, op, right):
        try:
            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            left_int = int(left)
            right_int = int(right)
            if op == "-": return left_int - right_int
            if op == "*": return left_int * right_int
            if op == "/": return left_int / right_int
            if op == "//": return left_int // right_int
            if op == "**": return left_int ** right_int
            if op == "%": return left_int % right_int
            if op == "&": return left_int & right_int
            if op == "|": return left_int | right_int
            if op == "^": return left_int ^ right_int
        except Exception:
            return 0
        return 0