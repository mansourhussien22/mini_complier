from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# استيراد الأدوات من ملف المترجم الخاص بك
try:
    from api.mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator
except ImportError:
    from mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator

app = FastAPI()

class CodePayload(BaseModel):
    source_code: str

@app.post("/compile")
def compile_code(payload: CodePayload):
    try:
        # 1. Lexical Analysis
        tokens = lexer(payload.source_code)
        tokens_list = [{"type": t.type, "value": t.value} for t in tokens]

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
                "tac": []
            }

        # 4. Three Address Code
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
        raise HTTPException(status_code=400, detail=str(e))