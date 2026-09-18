from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    from api.mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator
except ImportError:
    from mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator

app = FastAPI()

# قراءة ملف index.html من نفس مسار المجلد الحالي
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
    # تنظيف النص القادم من المتصفح والتخلص من نهايات أسطر ويندوز
    clean_code = payload.source_code.replace("\r\n", "\n").replace("\r", "\n").strip()

    tokens_list = []
    try:
        # 1. Lexer
        tokens = lexer(clean_code)
        tokens_list = [{"type": t.type, "value": str(t.value)} for t in tokens]

        # 2. Parser
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
                "tac": []
            }

        # 4. Code Generation
        generator = CodeGenerator()
        tac = generator.generate(ast)

        return {
            "success": True,
            "tokens": tokens_list,
            "syntax_tree": ast,
            "errors": [],
            "tac": tac
        }

    except Exception as e:
        # إرجاع أي خطأ نحوي أو معجمي في مصفوفة errors بدلاً من كود 400
        return {
            "success": False,
            "tokens": tokens_list,
            "syntax_tree": None,
            "errors": [str(e)],
            "tac": []
        }
