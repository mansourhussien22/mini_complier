from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    from api.mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator
except ImportError:
    from mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator

app = FastAPI()

# مسار ترحيبي للتأكد من عمل السيرفر
@app.get("/")
@app.get("/api")
def home():
    return {"message": "Compiler API is running! Go to /docs"}

class CodePayload(BaseModel):
    source_code: str

@app.post("/compile")
@app.post("/api/compile")
def compile_code(payload: CodePayload):
    try:
        tokens = lexer(payload.source_code)
        tokens_list = [{"type": t.type, "value": t.value} for t in tokens]

        parser = Parser(tokens)
        ast = parser.parse()

        errors = semantic_analysis(ast)
        if errors:
            return {
                "success": False,
                "tokens": tokens_list,
                "syntax_tree": ast,
                "errors": errors,
                "tac": []
            }

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