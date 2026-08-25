import os

disclaimer = "> **Note:** These features (including XP, leveling, and achievements) are additional extensions and are not part of the core functionality evaluated in the bachelor thesis.\n\n"

targets = [
    "docs/index.md",
    "docs/introduction.md",
    "docs/user-guide.md",
    "docs/commands.md",
    "docs/roles.md",
    "docs/integrations.md"
]

for t in targets:
    if os.path.exists(t):
        with open(t, 'r', encoding='utf-8') as f:
            content = f.read()
        if "These features" not in content:
            with open(t, 'w', encoding='utf-8') as f:
                f.write(disclaimer + content)
