"""Deterministic Lexical and Structural Scanning Layer for Polyglot Code Intelligence.

Phase 14 Remediation: Provides token-aware, comment-aware, string-aware, and
structure-aware lexical processing for JavaScript, TypeScript, and Java.

Guarantees:
1. Syntax-like tokens inside comments, string literals, and template literals are
   safely masked with whitespace, preserving exact 1-to-1 character offsets,
   line numbers, and column positions.
2. Generic type arguments (<...>) in declaration headers are structurally parsed
   and masked so they do not produce corrupted symbol names (e.g. 'UUID>') or
   cause declaration patterns to fail.
3. Import specifiers in real code (import ... from '...', require('...')) are
   preserved while impostor imports in strings/comments are neutralized.
"""

from dataclasses import dataclass
import re
from typing import Any

from pygments.lexers import JavaLexer, JavascriptLexer, TypeScriptLexer
from pygments.token import Token

from app.code_intelligence.contracts import CodeLanguage

# Regex to detect if '<' is preceded by a declaration keyword and identifier
_DECLARATION_GENERIC_PRECEDING = re.compile(
    r"""\b(?:class|interface|record|enum|function|type|extends|implements)\s+(?:[\w$]+\s*,\s*)*[\w$]+\s*$""",
    re.MULTILINE,
)

# Forbidden characters inside generic clauses in declaration headers
_FORBIDDEN_IN_DECLARATION_GENERICS = frozenset(";{}()=+*/!\"'`")


@dataclass(frozen=True)
class SourceToken:
    """Represents a deterministic source token with exact positional metadata."""
    token_type: Any
    value: str
    start_offset: int
    end_offset: int
    line: int
    column: int


class LexicalScanner:
    """Deterministic token scanner and structural masker for polyglot source code."""

    def __init__(self) -> None:
        self._js_lexer = JavascriptLexer(stripnl=False, ensurenl=False)
        self._ts_lexer = TypeScriptLexer(stripnl=False, ensurenl=False)
        self._java_lexer = JavaLexer(stripnl=False, ensurenl=False)

    def tokenize(self, content: str, language: CodeLanguage) -> list[SourceToken]:
        """Tokenize source content into a stream of SourceToken objects."""
        if language == CodeLanguage.JAVASCRIPT:
            lexer = self._js_lexer
        elif language == CodeLanguage.TYPESCRIPT:
            lexer = self._ts_lexer
        elif language == CodeLanguage.JAVA:
            lexer = self._java_lexer
        else:
            return []

        tokens: list[SourceToken] = []
        offset = 0
        line = 1
        col = 1

        for ttype, tval in lexer.get_tokens(content):
            start = offset
            tlen = len(tval)
            end = offset + tlen

            tokens.append(
                SourceToken(
                    token_type=ttype,
                    value=tval,
                    start_offset=start,
                    end_offset=end,
                    line=line,
                    column=col,
                )
            )

            lines = tval.split("\n")
            if len(lines) > 1:
                line += len(lines) - 1
                col = len(lines[-1]) + 1
            else:
                col += tlen
            offset = end

        return tokens

    def mask_non_code_regions(self, content: str, language: CodeLanguage) -> str:
        """Mask comments and non-import string literals with whitespace.
        
        Preserves 1-to-1 character lengths and newline positions so that line
        numbers and character offsets remain bit-for-bit identical to the source.
        """
        tokens = self.tokenize(content, language)
        if not tokens:
            return content

        # Identify non-whitespace tokens to check token adjacency/lookbehind
        non_ws_indices = [
            i for i, t in enumerate(tokens)
            if t.token_type not in Token.Text and t.token_type not in Token.Whitespace
        ]

        chars = list(content)

        for idx, tok in enumerate(tokens):
            ttype = tok.token_type
            start = tok.start_offset
            end = tok.end_offset

            # 1. Mask ALL comments (line comments, block comments, doc comments)
            if ttype in Token.Comment:
                for i in range(start, end):
                    if chars[i] != "\n":
                        chars[i] = " "
                continue

            # 2. Check if token is a string or character literal
            is_string = (
                ttype in Token.Literal.String
                or ttype in Token.Literal.Character
                or ttype == Token.String
            )

            if is_string:
                if language == CodeLanguage.JAVA:
                    # In Java, strings NEVER represent import modules or declarations
                    for i in range(start, end):
                        if chars[i] != "\n":
                            chars[i] = " "
                else:
                    # In JS/TS: only preserve strings that are actual import/require/export specifiers
                    curr_pos = None
                    for pos, orig_idx in enumerate(non_ws_indices):
                        if orig_idx == idx:
                            curr_pos = pos
                            break

                    is_import_string = False
                    if curr_pos is not None and curr_pos > 0:
                        prev_tok = tokens[non_ws_indices[curr_pos - 1]]
                        prev_val = prev_tok.value.strip()

                        # Case 1: import ... from "module" or export ... from "module"
                        if prev_val in ("from", "require"):
                            is_import_string = True
                        # Case 2: import "module" (side-effect import)
                        elif prev_val == "import":
                            is_import_string = True
                        # Case 3: require("module") or import("module")
                        elif prev_val == "(" and curr_pos > 1:
                            prev_prev = tokens[non_ws_indices[curr_pos - 2]]
                            if prev_prev.value.strip() in ("require", "import"):
                                is_import_string = True

                    if not is_import_string:
                        for i in range(start, end):
                            if chars[i] != "\n":
                                chars[i] = " "

        return "".join(chars)

    def mask_declaration_generics(self, content: str) -> str:
        """Replace generic clauses (<...>) in declaration headers with spaces.
        
        Only generic type clauses immediately following declaration keywords
        (class, interface, function, type, extends, implements) are masked.
        Preserves character offsets and line numbers.
        """
        chars = list(content)
        n = len(chars)
        i = 0

        while i < n:
            if chars[i] == "<":
                # Check if preceding code is a declaration header
                preceding_text = "".join(chars[max(0, i - 120) : i])
                if _DECLARATION_GENERIC_PRECEDING.search(preceding_text):
                    depth = 1
                    k = i + 1
                    is_valid = True
                    while k < n and depth > 0:
                        c = chars[k]
                        if c in _FORBIDDEN_IN_DECLARATION_GENERICS:
                            is_valid = False
                            break
                        elif c == "<":
                            depth += 1
                        elif c == ">":
                            depth -= 1
                        k += 1

                    if is_valid and depth == 0:
                        for pos in range(i, k):
                            if chars[pos] != "\n":
                                chars[pos] = " "
                        i = k
                        continue
            i += 1

        return "".join(chars)

    @staticmethod
    def split_balanced(
        text: str,
        delimiter: str = ",",
        open_bracket: str = "<",
        close_bracket: str = ">",
    ) -> list[str]:
        """Split text by delimiter, ignoring delimiters inside balanced brackets."""
        parts: list[str] = []
        current: list[str] = []
        depth = 0

        for char in text:
            if char == open_bracket:
                depth += 1
                current.append(char)
            elif char == close_bracket:
                if depth > 0:
                    depth -= 1
                current.append(char)
            elif char == delimiter and depth == 0:
                part = "".join(current).strip()
                if part:
                    parts.append(part)
                current = []
            else:
                current.append(char)

        if current:
            trailing = "".join(current).strip()
            if trailing:
                parts.append(trailing)

        return parts

    @staticmethod
    def strip_type_parameters(type_name: str) -> str:
        """Extract the base type name, removing any generic parameters."""
        clean: list[str] = []
        for char in type_name.strip():
            if char == "<":
                break
            clean.append(char)
        return "".join(clean).strip()
