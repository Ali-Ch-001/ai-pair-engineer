from pygments import lexers
from pygments.util import ClassNotFound


def detect_language(code: str) -> str:
    code_lower = code.lower()

    heuristic_signals = [
        ("TypeScript", ["interface ", "type ", ": string", ": number", ": boolean", "as const", "!:", "export type"]),
        ("JavaScript", ["const ", "let ", "function ", "=>", "import ", "require("]),
        ("Python", ["def ", "import ", "class ", "elif ", "print(", "self,", "self.", "from "]),
        ("Java", ["public class", "public static void", "system.out", "string[] args", "public ", "private ", "protected ", "void ", "static ", "new ", "extends ", "implements ", "@override"]),
        ("Go", ["func ", "package ", "fmt.", "err != nil", ":= "]),
        ("Rust", ["fn ", "let mut", "println!", "struct ", "impl "]),
        ("Ruby", ["def ", "puts ", "do |", "end", "require "]),
        ("SQL", ["select ", "from ", "where ", "insert into", "create table"]),
        ("HTML", ["<html", "<div", "<span", "<!doctype"]),
        ("CSS", ["margin:", "padding:", "color:", "font-size:", "background:", "display:"]),
        ("Shell", ["#!/bin/bash", "#!/bin/sh", "echo ", "export ", "fi", "done"]),
    ]

    best_lang = "Python"
    best_score = 0
    for lang, signals in heuristic_signals:
        score = sum(1 for s in signals if s in code_lower)
        if score > best_score:
            best_score = score
            best_lang = lang
    if best_score >= 1:
        return best_lang

    if code_lower.startswith("{") or code_lower.startswith("["):
        return "JSON"

    try:
        lexer = lexers.guess_lexer(code[:2000])
        name = lexer.name.lower()
        mapping = {
            "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
            "java": "Java", "ruby": "Ruby", "go": "Go", "rust": "Rust",
            "c": "C", "c++": "C++", "c#": "C#", "swift": "Swift",
            "kotlin": "Kotlin", "scala": "Scala", "php": "PHP",
            "sql": "SQL", "html": "HTML", "css": "CSS",
            "shell": "Shell", "bash": "Shell", "yaml": "YAML", "json": "JSON",
        }
        for key, value in mapping.items():
            if key in name:
                return value
        if "text only" in name or "text" == name:
            return "Python"
        return name.title()
    except ClassNotFound:
        return "Python"


def count_lines(code: str) -> int:
    return len(code.splitlines())
