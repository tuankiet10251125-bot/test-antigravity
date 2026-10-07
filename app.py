import os
import random
import re
import sqlite3
import string
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template_string,
    request,
    url_for,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-antigravity")
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            clicks INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def normalize_url(url):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def is_valid_url(url):
    regex = re.compile(
        r"^(https?://)"  # http:// or https://
        r"([a-zA-Z0-9.-]+(\.[a-zA-Z]{2,}))"  # domain
        r"(:\d+)?"  # port
        r"(/.*)?$",  # path
        re.IGNORECASE,
    )
    return re.match(regex, url) is not None


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mini URL Shortener</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #10b981;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2.5rem 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 760px;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .header h1 {
            font-size: 2.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .header p {
            color: var(--text-muted);
            font-size: 1rem;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.75rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            margin-bottom: 2rem;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        .input-row {
            display: flex;
            gap: 0.75rem;
        }
        input[type="text"] {
            flex: 1;
            padding: 0.85rem 1.15rem;
            border-radius: 0.65rem;
            border: 1px solid var(--border);
            background: #0f172a;
            color: var(--text-main);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
        }
        button.btn-primary {
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 0.65rem;
            padding: 0.85rem 1.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
            white-space: nowrap;
        }
        button.btn-primary:hover {
            background-color: var(--primary-hover);
        }
        button.btn-primary:active {
            transform: scale(0.98);
        }
        .flash-msg {
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid #ef4444;
            color: #fca5a5;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        .result-box {
            margin-top: 1.25rem;
            padding: 1.25rem;
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 0.75rem;
        }
        .result-title {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .result-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
        .short-url {
            color: #38bdf8;
            font-size: 1.05rem;
            font-weight: 600;
            text-decoration: none;
            word-break: break-all;
        }
        .short-url:hover {
            text-decoration: underline;
        }
        .btn-copy {
            background: #334155;
            color: #f8fafc;
            border: none;
            padding: 0.5rem 0.9rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: background 0.2s;
        }
        .btn-copy:hover {
            background: #475569;
        }
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }
        th, td {
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border);
        }
        th {
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        td.clicks {
            font-weight: 700;
            color: var(--success);
        }
        .empty-state {
            text-align: center;
            color: var(--text-muted);
            padding: 2rem 0;
            font-size: 0.95rem;
        }
        .footer {
            margin-top: auto;
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Mini URL Shortener</h1>
            <p>Rút gọn liên kết nhanh chóng, lưu trữ SQLite và theo dõi lượt click</p>
        </div>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash-msg">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="card">
            <form method="POST" action="/" class="form-group">
                <div class="input-row">
                    <input type="text" name="url" placeholder="Dán liên kết cần rút gọn (ví dụ: https://example.com/very-long-path)" required>
                    <button type="submit" class="btn-primary">Rút gọn</button>
                </div>
            </form>

            {% if new_short_url %}
            <div class="result-box">
                <div class="result-title">Liên kết rút gọn của bạn:</div>
                <div class="result-content">
                    <a href="{{ new_short_url }}" target="_blank" class="short-url" id="shortUrlDisplay">{{ new_short_url }}</a>
                    <button class="btn-copy" onclick="copyToClipboard('{{ new_short_url }}')">Sao chép</button>
                </div>
            </div>
            {% endif %}
        </div>

        <div class="card">
            <h2 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem;">Danh sách liên kết gần đây</h2>
            <div class="table-container">
                {% if urls %}
                <table>
                    <thead>
                        <tr>
                            <th>Mã rút gọn</th>
                            <th>Liên kết gốc</th>
                            <th>Lượt click</th>
                            <th>Ngày tạo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in urls %}
                        <tr>
                            <td>
                                <a href="{{ url_for('redirect_to_url', short_code=item['short_code'], _external=True) }}" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: 500;">
                                    {{ item['short_code'] }}
                                </a>
                            </td>
                            <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{{ item['original_url'] }}">
                                {{ item['original_url'] }}
                            </td>
                            <td class="clicks">{{ item['clicks'] }}</td>
                            <td style="color: var(--text-muted); font-size: 0.85rem;">{{ item['created_at'][:16] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty-state">Chưa có liên kết nào. Hãy nhập URL ở trên để tạo liên kết đầu tiên!</div>
                {% endif %}
            </div>
        </div>

        <div class="footer">
            Flask &bull; SQLite &bull; Python Web App
        </div>
    </div>

    <script>
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(function() {
                alert('Đã sao chép liên kết vào bộ nhớ tạm!');
            }).catch(function(err) {
                console.error('Không thể sao chép: ', err);
            });
        }
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    new_short_url = None

    if request.method == "POST":
        raw_url = request.form.get("url", "").strip()
        if not raw_url:
            flash("Vui lòng nhập URL hợp lệ.")
            return redirect(url_for("index"))

        normalized_url = normalize_url(raw_url)
        if not is_valid_url(normalized_url):
            flash("Định dạng URL không hợp lệ. Vui lòng kiểm tra lại.")
            return redirect(url_for("index"))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Tạo mã rút gọn duy nhất
        for _ in range(5):
            short_code = generate_short_code()
            try:
                cursor.execute(
                    "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
                    (normalized_url, short_code),
                )
                conn.commit()
                new_short_url = url_for("redirect_to_url", short_code=short_code, _external=True)
                break
            except sqlite3.IntegrityError:
                continue

        conn.close()

        if not new_short_url:
            flash("Không thể tạo mã rút gọn, vui lòng thử lại.")
            return redirect(url_for("index"))

    conn = get_db_connection()
    urls = conn.execute("SELECT * FROM urls ORDER BY id DESC LIMIT 15").fetchall()
    conn.close()

    return render_template_string(HTML_TEMPLATE, urls=urls, new_short_url=new_short_url)


@app.route("/<short_code>")
def redirect_to_url(short_code):
    conn = get_db_connection()
    url_entry = conn.execute(
        "SELECT * FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()

    if url_entry:
        conn.execute(
            "UPDATE urls SET clicks = clicks + 1 WHERE id = ?", (url_entry["id"],)
        )
        conn.commit()
        conn.close()
        return redirect(url_entry["original_url"])

    conn.close()
    return "<h1>404 - Không tìm thấy liên kết rút gọn này</h1>", 404


@app.route("/api/shorten", methods=["POST"])
def api_shorten():
    data = request.get_json(silent=True) or {}
    raw_url = data.get("url", "").strip()

    if not raw_url:
        return jsonify({"error": "Thiếu tham số url"}), 400

    normalized_url = normalize_url(raw_url)
    if not is_valid_url(normalized_url):
        return jsonify({"error": "URL không hợp lệ"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    short_code = None

    for _ in range(5):
        candidate_code = generate_short_code()
        try:
            cursor.execute(
                "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
                (normalized_url, candidate_code),
            )
            conn.commit()
            short_code = candidate_code
            break
        except sqlite3.IntegrityError:
            continue

    conn.close()

    if not short_code:
        return jsonify({"error": "Không thể tạo mã rút gọn"}), 500

    short_url = url_for("redirect_to_url", short_code=short_code, _external=True)
    return jsonify({
        "short_code": short_code,
        "short_url": short_url,
        "original_url": normalized_url,
    }), 201


@app.route("/api/stats/<short_code>")
def api_stats(short_code):
    conn = get_db_connection()
    entry = conn.execute(
        "SELECT short_code, original_url, clicks, created_at FROM urls WHERE short_code = ?",
        (short_code,),
    ).fetchone()
    conn.close()

    if not entry:
        return jsonify({"error": "Không tìm thấy liên kết"}), 404

    return jsonify({
        "short_code": entry["short_code"],
        "original_url": entry["original_url"],
        "clicks": entry["clicks"],
        "created_at": entry["created_at"],
    })


if __name__ == "__main__":
    init_db()
    print("Khởi chạy ứng dụng URL Shortener tại: http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
