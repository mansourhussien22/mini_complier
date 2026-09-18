import sys
import webview
from pathlib import Path

try:
    from api.mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator, TACInterpreter
except ImportError:
    from mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator, TACInterpreter


class CompilerBridge:
    def compile_code(self, source_code: str):
        clean_code = source_code.replace("\r\n", "\n").replace("\r", "\n").strip()
        tokens_list = []
        try:
            tokens = lexer(clean_code)
            tokens_list = [{"type": t.type, "value": str(t.value)} for t in tokens]

            parser = Parser(tokens)
            ast = parser.parse()

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

            generator = CodeGenerator()
            tac = generator.generate(ast)

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


def main():
    bridge = CompilerBridge()
    
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent

    html_file = base_dir / "api" / "index.html"

    window = webview.create_window(
        title="Mini Compiler Studio",
        url=str(html_file.resolve()),
        js_api=bridge,
        width=1340,
        height=860,
        min_size=(960, 640),
        background_color="#060a12"
    )
    
    # الإجبار الصريح على استخدام محرك Chromium الحديث
    webview.start(gui='edgechromium', debug=False)


if __name__ == "__main__":
    main()