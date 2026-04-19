import re
import sys
import concurrent.futures
from deep_translator import GoogleTranslator
TARGET_LANG = "SChinese"
TARGET_CODE = "zh-CN"
OUTPUT_FILE = "addon_schinese.txt"
INPUT_FILE = "addon_russian.txt"
KV_PATTERN = re.compile(r'^(\s*"[^"]+"\s*")([^"\\]*(?:\\.[^"\\]*)*)(".*)$')
TAG_PATTERN = re.compile(r'(<[^>]+>|\\[nrt"]|%[\w\.]+%?|%%|%\w+|{[^}]+})')

def protect_and_translate(text, translator):
    if not text.strip() or text.isnumeric():
        return text
    leading_spaces = len(text) - len(text.lstrip(' '))
    trailing_spaces = len(text) - len(text.rstrip(' '))
    clean_text = text.strip()
    placeholders = []
    def repl(match):
        placeholders.append(match.group(0))
        return f" __TAG{len(placeholders)-1}__ "

    protected_text = TAG_PATTERN.sub(repl, clean_text)
    try:
        translated_text = translator.translate(protected_text)
    except Exception as e:
        return text
    if '"' in translated_text:
        parts = translated_text.split('"')
        safe_text = ""
        for i, part in enumerate(parts[:-1]):
            safe_text += part + ('“' if i % 2 == 0 else '”')
        translated_text = safe_text + parts[-1]
    for i, tag in enumerate(placeholders):
        translated_text = re.sub(
            fr'\s*__TAG{i}__\s*', 
            lambda _, t=tag: t, 
            translated_text, 
            count=1, 
            flags=re.IGNORECASE
        )
        
    return (' ' * leading_spaces) + translated_text.strip() + (' ' * trailing_spaces)

def process_line(index, line):
    if '"Language"' in line and '"Russian"' in line:
        return index, line.replace('"Russian"', f'"{TARGET_LANG}"')

    match = KV_PATTERN.match(line)
    if match:
        prefix = match.group(1)
        original_value = match.group(2)
        suffix = match.group(3)
        if any(c.isalpha() for c in original_value):
            translator = GoogleTranslator(source='ru', target=TARGET_CODE)
            translated_value = protect_and_translate(original_value, translator)
            return index, f"{prefix}{translated_value}{suffix}\n"
    return index, line

def main():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Файл {INPUT_FILE} не найден!")
        return

    print(f"\n--- Начало быстрого перевода на {TARGET_LANG} ({TARGET_CODE}) ---")
    out_lines = [None] * len(lines)
    max_threads = 20
    completed = 0
    total = len(lines)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(process_line, i, line): i for i, line in enumerate(lines)}
        
        for future in concurrent.futures.as_completed(futures):
            index, translated_line = future.result()
            out_lines[index] = translated_line
            
            completed += 1
            sys.stdout.write(f"\rПереведено строк: {completed}/{total} ({(completed/total)*100:.1f}%)")
            sys.stdout.flush()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)
        
    print(f"\n\nГотово! Супер-быстрый перевод завершен и сохранен в {OUTPUT_FILE}")

if __name__ == '__main__':
    main()