import functools
import math
import operator
import re
import string

KEYWORDS = {"print", "True", "False", "None"}
OPERATORS = {
    "+",
    "-",
    "*",
    "/",
    "=",
    "+=",
    "-=",
    "*=",
    "/=",
    "**",
    "//",
    "&",
    "|",
    "^",
    "~",
    "%",
    "@",
}
SYMBOLS = {"(", ")", ";", ",", "$", "#"}


class Token:

  def __init__(self, token_type, value, line=1):
    self.type = token_type
    self.value = value
    self.line = line

  def to_dict(self):
    return {"type": self.type, "value": self.value, "line": self.line}

  def __repr__(self):
    return f"Token({self.type}, '{self.value}', line={self.line})"


# -----------------------------
# 1. Lexical Analysis
# -----------------------------


def lexer(source_code):
  tokens = []
  i = 0
  n = len(source_code)
  line = 1

  while i < n:
    char = source_code[i]

    if char == "\n":
      line += 1
      i += 1
      continue

    if char.isspace():
      i += 1
      continue

    if char == "#" and (i + 1 < n and source_code[i + 1].isalpha()):
      tokens.append(Token("SPECIAL", "#", line))
      i += 1
      continue
    elif char == "#":
      while i < n and source_code[i] != "\n":
        i += 1
      continue

    if source_code[i : i + 3] in ('"""', "'''"):
      quote = source_code[i : i + 3]
      i += 3
      while i < n and source_code[i : i + 3] != quote:
        if source_code[i] == "\n":
          line += 1
        i += 1
      i += 3
      continue

    two_char = source_code[i : i + 2]
    if two_char in {"+=", "-=", "*=", "/=", "**", "//", "&=", "|="}:
      tokens.append(Token("OPERATOR", two_char, line))
      i += 2
      continue

    if char in ('"', "'"):
      quote = char
      i += 1
      string_val = ""
      start_line = line
      while i < n and source_code[i] != quote:
        if source_code[i] == "\n":
          line += 1
        string_val += source_code[i]
        i += 1
      if i >= n:
        raise Exception(
            f"Lexer Error at line {start_line}: Unterminated string literal\n"
            f"Detail: Closing quote ({quote}) is missing before end of file.\n"
            f"Hint: Make sure every opened string literal has a matching closing"
            f" quote on the same block."
        )
      i += 1
      tokens.append(Token("STRING", string_val, start_line))
      continue

    if char.isalpha() or char in {"_", "$"}:
      word = ""
      while i < n and (source_code[i].isalnum() or source_code[i] in {"_", "$"}):
        word += source_code[i]
        i += 1

      if word in KEYWORDS:
        tokens.append(Token("KEYWORD", word, line))
      else:
        tokens.append(Token("IDENTIFIER", word, line))
      continue

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
      tokens.append(Token("NUMBER", number, line))
      continue

    if char in OPERATORS:
      tokens.append(Token("OPERATOR", char, line))
      i += 1
      continue

    if char in SYMBOLS:
      tokens.append(Token("SYMBOL", char, line))
      i += 1
      continue

    raise Exception(
        f"Lexer Error at line {line}: Unknown character '{char}'\n"
        f"Detail: Character '{char}' is not recognized as a valid operator,"
        " symbol, or identifier.\n"
        "Hint: Remove this invalid character or verify proper syntax."
    )

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
      raise Exception(
          "Parser Error: Unexpected end of code\nDetail: The parser reached the"
          " end of input while expecting further expressions or closing"
          " tokens.\nHint: Check for missing closing parentheses, operands, or"
          " statement terminators."
      )

    line_num = getattr(token, "line", 1)

    if token.type != token_type:
      found_val = token.value
      found_type = token.type
      hint_msg = (
          "This language uses direct assignment (e.g., x = 'text') rather than"
          " type keywords."
          if found_val in {"string", "int", "float", "double", "bool"}
          else "Verify the expected statement structure."
      )
      raise Exception(
          f"Syntax Error at line {line_num}: Expected {token_type}, got"
          f" '{found_val}' ({found_type})\n"
          f"Detail: The parser encountered '{found_val}' where a token of type"
          f" '{token_type}' was required.\n"
          f"Hint: {hint_msg}"
      )

    if value is not None and token.value != value:
      raise Exception(
          f"Syntax Error at line {line_num}: Expected '{value}', got"
          f" '{token.value}'\n"
          f"Detail: Statement expected explicit symbol or operator '{value}'.\n"
          f"Hint: Add or replace with the expected symbol '{value}'."
      )

    self.pos += 1
    return token

  def parse(self):
    statements = []
    while self.current_token() is not None:
      statements.append(self.parse_statement())
      if (
          self.current_token()
          and self.current_token().type == "SYMBOL"
          and self.current_token().value == ";"
      ):
        self.match("SYMBOL", ";")
    return statements

  def parse_statement(self):
    token = self.current_token()

    if token.type == "KEYWORD" and token.value == "print":
      return self.parse_print()

    if token.type == "IDENTIFIER":
      return self.parse_assignment()

    line_num = getattr(token, "line", 1)
    raise Exception(
        f"Syntax Error at line {line_num}: Invalid statement starting with"
        f" '{token.value}'\n"
        f"Detail: Statements must start with an assignment identifier or 'print'"
        " keyword.\n"
        f"Hint: Begin with a variable assignment (e.g., {token.value} = ...)"
        " or a print() statement."
    )

  def parse_assignment(self):
    var_token = self.match("IDENTIFIER")
    var_name = var_token.value
    line_num = var_token.line

    op_token = self.match("OPERATOR").value
    expression = self.parse_expression()

    if op_token != "=":
      base_op = op_token[0]
      expression = {
          "type": "binary_expression",
          "operator": base_op,
          "left": {"type": "identifier", "name": var_name, "line": line_num},
          "right": expression,
      }

    return {
        "type": "declaration",
        "name": var_name,
        "expression": expression,
        "line": line_num,
    }

  def parse_print(self):
    self.match("KEYWORD", "print")
    self.match("SYMBOL", "(")
    args = []
    if self.current_token() and not (
        self.current_token().type == "SYMBOL"
        and self.current_token().value == ")"
    ):
      args.append(self.parse_expression())
      while (
          self.current_token()
          and self.current_token().type == "SYMBOL"
          and self.current_token().value == ","
      ):
        self.match("SYMBOL", ",")
        args.append(self.parse_expression())

    self.match("SYMBOL", ")")
    return {"type": "print", "arguments": args}

  def parse_expression(self):
    left = self.parse_term()
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
            "right": right,
        }
      else:
        break
    return left

  def parse_term(self):
    token = self.current_token()

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
      return {
          "type": "identifier",
          "name": self.match("IDENTIFIER").value,
          "line": getattr(token, "line", 1),
      }

    line_num = getattr(token, "line", 1)
    raise Exception(
        f"Syntax Error at line {line_num}: Invalid expression term"
        f" '{token.value}'\n"
        f"Detail: Expected an operand (identifier, number, string, or"
        f" sub-expression) but found '{token.value}'.\n"
        "Hint: Check for missing operators, mismatched parentheses, or dangling"
        " punctuation."
    )


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
      var_name = expression["name"]
      line_num = expression.get("line", 1)
      if var_name not in declared_variables:
        errors.append(
            f"Semantic Error at line {line_num}: NameError: name '{var_name}'"
            " is not defined\n"
            f"Detail: Identifier '{var_name}' is referenced before declaration"
            " in current scope.\n"
            f"Hint: Initialize or declare '{var_name}' prior to reading it"
            f" (e.g., {var_name} = 0)."
        )
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

      if line.startswith("print "):
        content = line[6:].strip()
        args = self._split_args(content)
        resolved = [str(self._resolve_val(arg.strip())) for arg in args]
        self.stdout.append(" ".join(resolved))

      elif "=" in line:
        left, right = [part.strip() for part in line.split("=", 1)]

        if (right.startswith('"') and right.endswith('"')) or (
            right.startswith("'") and right.endswith("'")
        ):
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
    pattern = r',\s*(?=(?:[^\'"]*[\'"][^\'"]*[\'"])*[^\'"]*$)'
    return re.split(pattern, text)

  def _resolve_val(self, token):
    token = token.strip()
    if (token.startswith('"') and token.endswith('"')) or (
        token.startswith("'") and token.endswith("'")
    ):
      return token[1:-1]

    if token == "True":
      return True
    if token == "False":
      return False
    if token == "None":
      return None

    if token.replace(".", "", 1).isdigit():
      return float(token) if "." in token else int(token)

    if token in self.env:
      return self.env[token]

    raise Exception(
        f"Runtime Error: Variable '{token}' is not defined.\n"
        f"Detail: Attempted to access or evaluate '{token}' in runtime without"
        " binding.\n"
        f"Hint: Ensure variable '{token}' is assigned a value prior to usage."
    )

def _eval_op(self, left, op, right):
        # 1. التعامل مع النصوص: الجمع فقط مسموح
        if isinstance(left, str) or isinstance(right, str):
            if op == "+":
                return str(left) + str(right)
            raise Exception(
                f"TypeError: unsupported operand type(s) for {op}: '{type(left).__name__}' and '{type(right).__name__}'\n"
                f"Detail: Cannot use arithmetic operator '{op}' on text data ('{left}' {op} '{right}').\n"
                f"Hint: Strings only support concatenation via the '+' operator."
            )

        # 2. فحص القسمة على صفر
        if op in {"/", "//", "%"} and (right == 0 or right == "0"):
            raise Exception(
                f"ZeroDivisionError: division by zero\n"
                f"Detail: Denominator evaluated to zero during '{op}' operation.\n"
                f"Hint: Ensure the divisor expression does not evaluate to 0."
            )

        # 3. معالجة الأرقام (صحيحة وعشرية)
        try:
            l_val = float(left) if isinstance(left, (int, float)) or "." in str(left) else int(left)
            r_val = float(right) if isinstance(right, (int, float)) or "." in str(right) else int(right)

            if op == "+": res = l_val + r_val
            elif op == "-": res = l_val - r_val
            elif op == "*": res = l_val * r_val
            elif op == "/": res = l_val / r_val
            elif op == "//": res = int(l_val) // int(r_val)
            elif op == "**": res = l_val ** r_val
            elif op == "%": res = int(l_val) % int(r_val)
            elif op == "&": res = int(l_val) & int(r_val)
            elif op == "|": res = int(l_val) | int(r_val)
            elif op == "^": res = int(l_val) ^ int(r_val)
            else:
                raise Exception(f"Unsupported operator: {op}")

            # إرجاع عدد صحيح إذا كان الناتج بدون كسور
            return int(res) if isinstance(res, float) and res.is_integer() else res

        except ValueError:
            raise Exception(
                f"TypeError: invalid operand value\n"
                f"Detail: Failed to parse '{left}' or '{right}' into a valid numeric representation.\n"
                f"Hint: Check the data types of variables participating in this expression."
            )