import re
from collections import Counter

ALLOWED_LEVELS = {"ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"}

OLD_PATTERN = re.compile(r'\b(ERROR|WARNING|INFO|DEBUG|CRITICAL)\b', re.IGNORECASE)

START_LINE_PREFIX_NEW = re.compile(
    r'^\s*'
    r'(?:'
    r'\[?\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}'
    r'|'
    r'\[[^\]]+\]'
    r')'
)
FIRST_LEVEL_TOKEN_NEW = re.compile(r'\b(ERROR|WARNING|INFO|DEBUG|CRITICAL)\b')


def parse_old(file_path):
    counts = Counter()
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = OLD_PATTERN.search(line)
            if m:
                lvl = m.group(1).upper()
                if lvl in ALLOWED_LEVELS:
                    counts[lvl] += 1
    return counts


def parse_new(file_path):
    counts = Counter()
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not START_LINE_PREFIX_NEW.search(line):
                continue
            m = FIRST_LEVEL_TOKEN_NEW.search(line)
            if m:
                lvl = m.group(1)
                if lvl in ALLOWED_LEVELS:
                    counts[lvl] += 1
    return counts


if __name__ == "__main__":
    path = r"E:\temp\record13\293\sample.log"
    print("=== 旧逻辑（逐行单词匹配，有 Bug）===")
    old = parse_old(path)
    for lvl in ["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"]:
        print(f"  {lvl}: {old[lvl]}")
    print(f"  total: {sum(old.values())}")
    print()
    print("=== 新逻辑（仅识别日志起始行，已修复）===")
    new = parse_new(path)
    for lvl in ["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"]:
        print(f"  {lvl}: {new[lvl]}")
    print(f"  total: {sum(new.values())}")
    print()
    expected = Counter({"INFO": 10, "WARNING": 5, "ERROR": 5, "DEBUG": 2, "CRITICAL": 1})
    print("=== 期望值 ===")
    for lvl in ["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"]:
        print(f"  {lvl}: {expected[lvl]}")
    print(f"  total: {sum(expected.values())}")
    print()
    ok = all(new[lvl] == expected[lvl] for lvl in ALLOWED_LEVELS)
    print(f"修复验证结果: {'PASS ✓' if ok else 'FAIL ✗'}")
