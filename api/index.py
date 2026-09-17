from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    from api.mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator
except ImportError:
    from mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator

app = FastAPI(title="Mini Compiler Studio")

class CodePayload(BaseModel):
    source_code: str

# HTML & UI Template
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mini Compiler Studio</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; }
    pre, code, textarea { font-family: 'Fira Code', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-4 md:p-8">
  <div class="max-w-7xl mx-auto space-y-6">
    
    <!-- Header -->
    <header class="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-5 gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <span class="p-2 bg-indigo-600 rounded-lg text-sm font-mono">⚡</span> Mini Compiler Studio
        </h1>
        <p class="text-xs text-slate-400 mt-1">Lexical, Syntax, Semantic, and Three Address Code Generator</p>
      </div>
      <button id="runBtn" onclick="runCompiler()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2.5 rounded-lg font-medium transition shadow-lg shadow-indigo-600/20 active:scale-95 flex items-center justify-center gap-2">
        <span>Run Compiler</span> ➜
      </button>
    </header>

    <!-- Main Grid Layout (Blocks) -->
    <main class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- Block 1: Editor -->
      <section class="lg:col-span-5 flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div class="bg-slate-800/60 px-4 py-2.5 border-b border-slate-800 flex justify-between items-center">
          <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">1. Source Code</span>
          <span class="text-xs text-slate-500">C-like Syntax</span>
        </div>
        <textarea id="codeEditor" rows="18" class="w-full flex-1 bg-transparent p-4 text-emerald-400 focus:outline-none resize-none text-sm leading-relaxed" placeholder="Write code here...">int x = 5;
int y = x + 3;
print(y);</textarea>
      </section>

      <!-- Blocks Container -->
      <section class="lg:col-span-7 grid grid-cols-1 md:grid-cols-2 gap-4">
        
        <!-- Block 2: Tokens -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
          <div class="bg-slate-800/60 px-4 py-2 border-b border-slate-800">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">2. Lexical Tokens</span>
          </div>
          <div id="tokensBox" class="p-4 h-56 overflow-y-auto flex flex-wrap content-start gap-1.5 text-xs">
            <span class="text-slate-500 italic">Click Run to generate tokens...</span>
          </div>
        </div>

        <!-- Block 3: Semantic Status -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
          <div class="bg-slate-800/60 px-4 py-2 border-b border-slate-800">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">3. Semantic Analysis</span>
          </div>
          <div id="semanticBox" class="p-4 h-56 overflow-y-auto text-xs flex flex-col justify-center items-center">
            <span class="text-slate-500 italic">Semantic status will appear here</span>
          </div>
        </div>

        <!-- Block 4: AST -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
          <div class="bg-slate-800/60 px-4 py-2 border-b border-slate-800">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">4. Syntax Tree (AST)</span>
          </div>
          <pre id="astBox" class="p-4 h-64 overflow-y-auto text-xs text-amber-400/90 whitespace-pre-wrap leading-relaxed"><span class="text-slate-500 italic">AST will appear here...</span></pre>
        </div>

        <!-- Block 5: TAC -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
          <div class="bg-slate-800/60 px-4 py-2 border-b border-slate-800">
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">5. Three Address Code (TAC)</span>
          </div>
          <pre id="tacBox" class="p-4 h-64 overflow-y-auto text-xs text-sky-400 whitespace-pre-wrap leading-relaxed"><span class="text-slate-500 italic">TAC instructions will appear here...</span></pre>
        </div>

      </section>
    </main>
  </div>

  <script>
    async function runCompiler() {
      const code = document.getElementById('codeEditor').value;
      const btn = document.getElementById('runBtn');
      btn.innerText = "Compiling...";
      btn.disabled = true;

      try {
        const response = await fetch('/compile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source_code: code })
        });
        
        const data = await response.json();

        // 1. Tokens Rendering
        const tokensBox = document.getElementById('tokensBox');
        tokensBox.innerHTML = '';
        if (data.tokens && data.tokens.length > 0) {
          data.tokens.forEach(t => {
            const badge = document.createElement('span');
            badge.className = "px-2 py-1 rounded bg-slate-800 border border-slate-700 font-mono";
            badge.innerHTML = `<span class="text-indigo-400 text-[10px]">${t.type}</span>: <span class="text-white">${t.value}</span>`;
            tokensBox.appendChild(badge);
          });
        }

        // 2. Semantic Analysis Rendering
        const semanticBox = document.getElementById('semanticBox');
        if (data.errors && data.errors.length > 0) {
          semanticBox.innerHTML = `
            <div class="w-full bg-red-950/40 border border-red-800/50 p-3 rounded-lg text-red-300">
              <p class="font-bold mb-1">❌ Semantic Errors Detected:</p>
              <ul class="list-disc list-inside space-y-1">
                ${data.errors.map(err => `<li>${err}</li>`).join('')}
              </ul>
            </div>`;
        } else {
          semanticBox.innerHTML = `
            <div class="w-full text-center p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-lg text-emerald-400">
              ✓ No Errors Found (Clean Code)
            </div>`;
        }

        // 3. AST Rendering
        document.getElementById('astBox').textContent = JSON.stringify(data.syntax_tree, null, 2);

        // 4. TAC Rendering
        const tacBox = document.getElementById('tacBox');
        if (data.tac && data.tac.length > 0) {
          tacBox.textContent = data.tac.join('\\n');
        } else {
          tacBox.textContent = "// No TAC generated due to errors or empty output";
        }

      } catch (err) {
        alert("Compilation failed: " + err.message);
      } finally {
        btn.innerText = "Run Compiler ➜";
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_ui():
    return HTML_CONTENT

@app.post("/compile")
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