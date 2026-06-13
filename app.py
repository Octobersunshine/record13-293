import re
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

LOG_LEVEL_PATTERN = re.compile(r'\b(ERROR|WARNING|INFO|DEBUG|CRITICAL)\b', re.IGNORECASE)

ALLOWED_LEVELS = {"ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"}


def parse_log_counts(file_path):
    counts = {level: 0 for level in ALLOWED_LEVELS}
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            match = LOG_LEVEL_PATTERN.search(line)
            if match:
                level = match.group(1).upper()
                if level in counts:
                    counts[level] += 1
    return counts


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
        counts = parse_log_counts(tmp_path)
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
    }
    return jsonify(result), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
