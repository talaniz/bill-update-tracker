from pathlib import Path


REQUIRED_PATHS = [
    "AGENTS.md",
    "PROMPTS.md",
    "GOALS.md",
    "harness/build/phase-00-harness-scaffold.md",
    "harness/context/phase-00-harness-scaffold_context.md",
    "harness/code_review/phase-00-harness-scaffold_context.md",
]


def main() -> int:
    missing = [path for path in REQUIRED_PATHS if not Path(path).exists()]
    if missing:
        for path in missing:
            print(f"missing: {path}")
        return 1
    print("harness ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

