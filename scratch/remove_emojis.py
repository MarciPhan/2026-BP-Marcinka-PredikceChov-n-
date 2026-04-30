import os
import unicodedata

def is_emoji(char):
    category = unicodedata.category(char)
    if category in ('So', 'Cn'):
        return True
    if 0x1F300 <= ord(char) <= 0x1F9FF:
        return True
    if 0x2600 <= ord(char) <= 0x26FF:
        return True
    if 0x2700 <= ord(char) <= 0x27BF:
        return True
    if 0xFE00 <= ord(char) <= 0xFE0F:
        return True
    return False

def remove_emojis_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = "".join(c for c in content if not is_emoji(c))
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

target_dirs = ['docs-site', 'docs', '.'] # include root for README.md
modified_files = []

for target_dir in target_dirs:
    for root, dirs, files in os.walk(target_dir):
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        if '.venv' in dirs:
            dirs.remove('.venv')
        if '.git' in dirs:
            dirs.remove('.git')
        
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                # Avoid processing files multiple times if they are in subdirectories of target_dirs
                abs_path = os.path.abspath(file_path)
                if abs_path in [os.path.abspath(f) for f in modified_files]:
                    continue
                    
                if remove_emojis_from_file(file_path):
                    modified_files.append(file_path)

print(f"Modified {len(modified_files)} files:")
for f in modified_files:
    print(f)
