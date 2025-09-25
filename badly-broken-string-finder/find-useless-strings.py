import ast
import getpass
import os
from typing import List, Optional, Tuple


def get_python_files_in_subdirs():
    user = getpass.getuser()

    directory_list = [
        f"/home/{user}/Documents/folder1",
        f"/home/{user}/Documents/folder2"
    ]
    python_files = []

    for directory in directory_list:
        for dirpath, _, filenames in os.walk(directory):
            for filename in [f for f in filenames if f.lower().endswith((".py"))]:
                python_files.append(os.path.abspath(os.path.join(dirpath, filename)))

    return python_files


def _is_stringy(value: ast.AST) -> bool:
    return (isinstance(value, ast.Constant) and isinstance(value.value, str)) or isinstance(
        value, ast.JoinedStr
    )


def _is_triple_quoted(seg: str) -> bool:
    """
    Detect if the *source* uses triple quotes, allowing r/R/u/U/b/B prefixes.
    (f/F is excluded here because f-strings are not ast.Constant anyway.)
    """
    i = 0
    while i < len(seg) and seg[i] in "rRuUbB":
        i += 1
    return seg[i : i + 3] in ('"""', "'''")


def _is_comment_like_string(node: ast.AST, code: str) -> bool:
    """
    Returns True iff `node` is a *plain* string literal (not f-string) that
    should be treated like a comment:
      - multi-line plain strings, or
      - single-line but triple-quoted plain strings.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        seg: Optional[str] = ast.get_source_segment(code, node)
        if seg is not None:
            if "\n" in seg:
                return True
            if _is_triple_quoted(seg):
                return True
        # Fallback if we couldn't get the exact source
        return "\n" in node.value
    return False  # Never treat JoinedStr (f-strings) as comments


class UselessStringVisitor(ast.NodeVisitor):
    def __init__(self, code: str) -> None:
        self.code = code
        self.findings: List[Tuple[int, int, str, str]] = []  # (lineno, col, msg, snippet)

    def _snippet(self, value: ast.AST) -> str:
        seg: Optional[str] = ast.get_source_segment(self.code, value)
        if seg is not None:
            return seg
        try:
            return ast.unparse(value)  # Py 3.9+
        except Exception:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return repr(value.value)
            return "<string-literal>"

    def _check_body(self, body):
        # Skip a leading docstring
        start_idx = (
            1 if body and isinstance(body[0], ast.Expr) and _is_stringy(body[0].value) else 0
        )
        for node in body[start_idx:]:
            if isinstance(node, ast.Expr) and _is_stringy(node.value):
                # Ignore comment-like *plain* string literals anywhere
                if _is_comment_like_string(node.value, self.code):
                    continue
                snippet = self._snippet(node.value)
                self.findings.append(
                    (node.lineno, node.col_offset, "useless string literal", snippet)
                )

    def visit_Module(self, node: ast.Module):
        self._check_body(node.body)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_body(node.body)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_body(node.body)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._check_body(node.body)
        self.generic_visit(node)


def find_useless_string_literals(code: str) -> List[Tuple[int, int, str, str]]:
    tree = ast.parse(code)
    v = UselessStringVisitor(code)
    v.visit(tree)
    return v.findings


def main():
    file_list = get_python_files_in_subdirs()

    for file in file_list:
        with open(file, "r", encoding="utf-8") as f:
            code = f.read()
        for lineno, col, msg, snippet in find_useless_string_literals(code):
            print(f"---\n{file}: line {lineno}:{col}:\n{msg}:\n{snippet}\n")


if __name__ == "__main__":
    main()
