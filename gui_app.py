import json
import tkinter as tk
from tkinter import ttk, scrolledtext

# استيراد أدوات الكومبايلر من ملفك
try:
    from api.mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator
except ImportError:
    from mini_compiler import lexer, Parser, semantic_analysis, CodeGenerator


class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Compiler - Desktop Studio")
        self.root.geometry("1100;750".replace(";", "x"))
        self.root.configure(bg="#0f172a")  # Dark Slate Background

        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#1e293b", height=50)
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        title = tk.Label(
            header_frame,
            text="⚡ Mini Compiler Studio (Desktop)",
            font=("Segoe UI", 14, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        title.pack(side=tk.LEFT, padx=15, pady=10)

        run_btn = tk.Button(
            header_frame,
            text="▶ Run Compiler",
            font=("Segoe UI", 10, "bold"),
            bg="#4f46e5",
            fg="white",
            activebackground="#4338ca",
            activeforeground="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.run_compiler_logic
        )
        run_btn.pack(side=tk.RIGHT, padx=15, pady=8)

        # Main Container (2 Columns)
        main_frame = tk.Frame(self.root, bg="#0f172a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Column: Code Editor
        left_frame = tk.LabelFrame(
            main_frame,
            text=" 1. Source Code ",
            font=("Segoe UI", 10, "bold"),
            fg="#94a3b8",
            bg="#1e293b",
            bd=1
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.editor = scrolledtext.ScrolledText(
            left_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#020617",
            fg="#34d399",
            insertbackground="white",
            bd=0
        )
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.editor.insert(tk.END, "int x = 5;\nint y = x + 3;\nprint(y);")

        # Right Column: Blocks (Grid 2x2)
        right_frame = tk.Frame(main_frame, bg="#0f172a")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(1, weight=1)

        # Block 2: Tokens
        self.tokens_box = self.create_block(right_frame, " 2. Lexical Tokens ", 0, 0, "#818cf8")
        
        # Block 3: Semantic Status
        self.semantic_box = self.create_block(right_frame, " 3. Semantic Analysis ", 0, 1, "#f43f5e")

        # Block 4: AST
        self.ast_box = self.create_block(right_frame, " 4. Syntax Tree (AST) ", 1, 0, "#fbbf24")

        # Block 5: TAC
        self.tac_box = self.create_block(right_frame, " 5. Three Address Code (TAC) ", 1, 1, "#38bdf8")

    def create_block(self, parent, title, row, col, fg_color):
        frame = tk.LabelFrame(
            parent,
            text=title,
            font=("Segoe UI", 9, "bold"),
            fg="#94a3b8",
            bg="#1e293b",
            bd=1
        )
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

        text_widget = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#020617",
            fg=fg_color,
            bd=0
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return text_widget

    def run_compiler_logic(self):
        source_code = self.editor.get("1.0", tk.END).strip()

        # تفريغ الخانات السابقة
        for box in [self.tokens_box, self.semantic_box, self.ast_box, self.tac_box]:
            box.delete("1.0", tk.END)

        try:
            # 1. Lexical Analysis
            tokens = lexer(source_code)
            tokens_str = "\n".join([f"{t.type:<12} : {t.value}" for t in tokens])
            self.tokens_box.insert(tk.END, tokens_str)

            # 2. Syntax Analysis
            parser = Parser(tokens)
            ast = parser.parse()
            self.ast_box.insert(tk.END, json.dumps(ast, indent=2))

            # 3. Semantic Analysis
            errors = semantic_analysis(ast)
            if errors:
                self.semantic_box.insert(tk.END, "❌ Errors Found:\n" + "\n".join(errors))
            else:
                self.semantic_box.insert(tk.END, "✔ No Errors (Valid Program)")

                # 4. TAC (يتم تنفيذه فقط في حالة عدم وجود أخطاء)
                generator = CodeGenerator()
                tac = generator.generate(ast)
                self.tac_box.insert(tk.END, "\n".join(tac))

        except Exception as e:
            self.semantic_box.insert(tk.END, f"Syntax/Lexical Error:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CompilerGUI(root)
    root.mainloop()