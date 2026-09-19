import sys
from pathlib import Path
import webview

try:
  from api.mini_compiler import (
      CodeGenerator,
      Parser,
      TACInterpreter,
      lexer,
      semantic_analysis,
  )
except ImportError:
  from mini_compiler import (
      CodeGenerator,
      Parser,
      TACInterpreter,
      lexer,
      semantic_analysis,
  )


class CompilerBridge:

  def _format_error(self, err_text: str):
    """تحويل نص الخطأ إلى كائن منظم يحتوي على Stage و Message و Detail."""
    lines = str(err_text).split("\n", 1)
    title_msg = lines[0].strip()
    detail_msg = lines[1].strip() if len(lines) > 1 else ""

    # استنتاج مرحلة الخطأ تلقائياً
    stage = "Parser"
    if "Lexer" in title_msg:
      stage = "Lexer"
    elif "Semantic" in title_msg or "NameError" in title_msg:
      stage = "Semantic"
    elif "Runtime" in title_msg:
      stage = "Runtime"

    return {"stage": stage, "message": title_msg, "detail": detail_msg}

  def compile_code(self, source_code: str):
    clean_code = source_code.replace("\r\n", "\n").replace("\r", "\n").strip()
    tokens_list = []

    try:
      tokens = lexer(clean_code)
      tokens_list = [
          t.to_dict()
          if hasattr(t, "to_dict")
          else {"type": t.type, "value": str(t.value)}
          for t in tokens
      ]

      parser = Parser(tokens)
      ast = parser.parse()

      semantic_errs = semantic_analysis(ast)
      if semantic_errs:
        formatted_errors = [self._format_error(err) for err in semantic_errs]
        return {
            "success": False,
            "tokens": tokens_list,
            "syntax_tree": ast,
            "errors": formatted_errors,
            "tac": [],
            "output": [],
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
          "output": output,
      }

    except Exception as e:
      return {
          "success": False,
          "tokens": tokens_list,
          "syntax_tree": None,
          "errors": [self._format_error(str(e))],
          "tac": [],
          "output": [],
      }


def main():
  bridge = CompilerBridge()

  if getattr(sys, "frozen", False):
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
      background_color="#060a12",
  )

  # الإجبار الصريح على استخدام محرك Chromium الحديث
  webview.start(gui="edgechromium", debug=False)


if __name__ == "__main__":
  main()