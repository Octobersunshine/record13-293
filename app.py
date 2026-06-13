import re
import tempfile
from collections import Counter
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

ALLOWED_LEVELS = {"ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"}
ERROR_LEVELS = {"ERROR", "CRITICAL"}
TOP_N = 5

START_LINE_PREFIX = re.compile(
    r'^\s*'
    r'(?:'
    r'\[?\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}'
    r'|'
    r'\[[^\]]+\]'
    r')'
)

FIRST_LEVEL_TOKEN = re.compile(r'\b(ERROR|WARNING|INFO|DEBUG|CRITICAL)\b')

MESSAGE_NORMALIZE_PATTERNS = [
    (re.compile(r'\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\s*'), ''),
    (re.compile(r'\b(?:ERROR|WARNING|INFO|DEBUG|CRITICAL)\b\s*'), ''),
    (re.compile(r'\[?\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}\]?\s*'), ''),
]


def _normalize_message(text):
    for pattern, replacement in MESSAGE_NORMALIZE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()


def parse_log(file_path):
    counts = {level: 0 for level in ALLOWED_LEVELS}
    error_messages = Counter()
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not START_LINE_PREFIX.search(line):
                continue
            match = FIRST_LEVEL_TOKEN.search(line)
            if not match:
                continue
            level = match.group(1)
            if level not in counts:
                continue
            counts[level] += 1
            if level in ERROR_LEVELS:
                end = match.end()
                message_text = line[end:]
                message = _normalize_message(message_text)
                if message:
                    error_messages[message] += 1

    top_errors = [
        {"message": msg, "count": cnt}
        for msg, cnt in error_messages.most_common(TOP_N)
    ]
    return counts, top_errors


@app.route("/upload", methods=["POST"])
def upload_log():
    if "file" not in request.files:
        return jsonify({"error": "未提供日志文件，请通过 file 字段上传"}), 400

    uploaded = request.files["file"]
    if uploaded.filename == "":
        return jsonify({"error": "文件名为空"}), 400

    suffix = Path(uploaded.filename).suffix or ".log"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
        uploaded.save(tmp)
        tmp_path = tmp.name

    try:
        counts, top_errors = parse_log(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    result = {
        "filename": uploaded.filename,
        "ERROR": counts["ERROR"],
        "WARNING": counts["WARNING"],
        "INFO": counts["INFO"],
        "DEBUG": counts["DEBUG"],
        "CRITICAL": counts["CRITICAL"],
        "total": sum(counts.values()),
        "top_errors": top_errors,
    }
    return jsonify(result), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
