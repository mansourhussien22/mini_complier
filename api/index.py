from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    from api.mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator, TACInterpreter
except ImportError:
    from mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator, TACInterpreter

app = FastAPI()
HTML_FILE_PATH = Path(__file__).parent / "index.html"


@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
def serve_ui():
    if not HTML_FILE_PATH.exists():
        return HTMLResponse("<h1>index.html not found!</h1>", status_code=404)
    return HTMLResponse(content=HTML_FILE_PATH.read_text(encoding="utf-8"))


class CodePayload(BaseModel):
    source_code: str


@app.post("/compile")
@app.post("/api/compile")
def compile_code(payload: CodePayload):
    clean_code = payload.source_code.replace("\r\n", "\n").replace("\r", "\n").strip()
    tokens_list = []

    try:
        # 1. Lexical Analysis
        tokens = lexer(clean_code)
        tokens_list = [{"type": t.type, "value": str(t.value)} for t in tokens]

        # 2. Syntax Analysis
        parser = Parser(tokens)
        ast = parser.parse()

        # 3. Semantic Analysis
        errors = semantic_analysis(ast)
        if errors:
            return {
                "success": False,
                "tokens": tokens_list,
                "syntax_tree": ast,
                "errors": errors,
                "tac": [],
                "output": []
            }

        # 4. Three Address Code (TAC)
        generator = CodeGenerator()
        tac = generator.generate(ast)

        # 5. Program Execution (Output / Stdout)
        interpreter = TACInterpreter(tac)
        output = interpreter.run()

        return {
            "success": True,
            "tokens": tokens_list,
            "syntax_tree": ast,
            "errors": [],
            "tac": tac,
            "output": output
        }

    except Exception as e:
        return {
            "success": False,
            "tokens": tokens_list,
            "syntax_tree": None,
            "errors": [str(e)],
            "tac": [],
            "output": []
        }