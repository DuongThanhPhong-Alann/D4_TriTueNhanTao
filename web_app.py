from flask import Flask, render_template_string, request, redirect, url_for, send_file
import pandas as pd
from doangiaxe import DuDoanGiaXeOtoCu  # Import lớp từ file doangiaxe.py
import os
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# Khởi tạo Flask app
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ROWS_PER_PAGE = 10  # Số dòng hiển thị mỗi trang

# Trang chủ (HTML với chủ đề Giáng Sinh)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dự Đoán Giá Xe Ô Tô Cũ</title>
    <style>
        body {
            font-family: "Arial", sans-serif;
            background: url('https://www.publicdomainpictures.net/pictures/320000/velka/snow-background-1606833637jGZ.jpg') no-repeat center center fixed;
            background-size: cover;
            color: #ffffff;
        }
        h1 {
            text-align: center;
            color: #FFD700;
            text-shadow: 2px 2px 5px #FF4500;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 20px;
        }
        .header-left {
            font-size: 1.5em;
            color: #FFD700;
            text-shadow: 2px 2px 5px #FF4500;
        }
        .header-right {
            font-size: 1em;
            color: #FFD700;
            text-align: right;
        }
        form {
            text-align: center;
            margin-top: 20px;
        }
        label {
            font-size: 1.2em;
            margin-right: 10px;
        }
        input[type="file"] {
            padding: 10px;
            font-size: 1em;
        }
        button {
            padding: 10px 20px;
            font-size: 1em;
            background-color: #FF4500;
            color: #FFFFFF;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        button:hover {
            background-color: #FFD700;
            color: #FF4500;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            Tên Nhóm: AIIA | HUTECH Đại Học Công Nghệ Thành Phố Hồ Chí Minh
        </div>
        <div class="header-right">
            <a href="{{ url_for('predict', filename=filename, page=1) }}">🎁 Tải về kết quả đầy đủ 🎁</a>
        </div>
    </div>
    <h1>🎄 Dự Đoán Giá Xe Ô Tô Cũ 🎅</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <label for="file">🎁 Chọn file CSV:</label>
        <input type="file" name="file" id="file">
        <button type="submit">✨ Tải lên và Dự đoán ✨</button>
    </form>

    <!-- Hiển thị hình ảnh biểu đồ dự đoán kết quả -->
    {% if chart_url %}
    <div style="text-align: center; margin-top: 40px;">
        <h3>Biểu đồ dự đoán giá ô tô</h3>
        <img src="{{ chart_url }}" alt="Chart" width="800" style="max-width: 100%; height: auto;" />
    </div>
    {% endif %}
</body>
</html>
"""

# Trang kết quả với chủ đề Giáng Sinh
RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kết Quả Dự Đoán</title>
    <style>
        body {
            font-family: "Arial", sans-serif;
            background: url('https://cdn.pixabay.com/photo/2016/11/25/18/34/snow-1850061_960_720.jpg') no-repeat center center fixed;
            background-size: cover;
            color: #ffffff;
        }
        h1 {
            text-align: center;
            color: #FFD700;
            text-shadow: 2px 2px 5px #FF4500;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 20px;
        }
        .header-left {
            font-size: 1.5em;
            color: #FFD700;
            text-shadow: 2px 2px 5px #FF4500;
        }
        .header-right {
            font-size: 1em;
            color: #FFD700;
            text-align: right;
        }
        table {
            margin: auto;
            border-collapse: collapse;
            width: 90%;
            background-color: rgba(255, 255, 255, 0.8);
            color: #000;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }
        th {
            background-color: #FF4500;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
        .pagination {
            text-align: center;
            margin-top: 20px;
        }
        .pagination a {
            margin: 0 5px;
            text-decoration: none;
            color: #FFD700;
            font-weight: bold;
        }
        .pagination a:hover {
            color: #FF4500;
        }
        .page-input {
            text-align: center;
            margin-top: 20px;
        }
        .page-input input {
            padding: 10px;
            font-size: 1em;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            Tên Nhóm: AIIA | HUTECH Đại Học Công Nghệ Thành Phố Hồ Chí Minh
        </div>
        <div class="header-right">
            <a href="{{ file_url }}">🎁 Tải về kết quả đầy đủ 🎁</a>
        </div>
    </div>
    <h1>🎁 Kết Quả Dự Đoán 🎁</h1>

    <!-- Hiển thị hình ảnh biểu đồ dự đoán kết quả -->
    {% if chart_url %}
    <div style="text-align: center; margin-top: 40px;">
        <h3>Biểu đồ dự đoán giá ô tô</h3>
        <img src="{{ chart_url }}" alt="Chart" width="800" style="max-width: 100%; height: auto;" />
        <p>Biểu đồ trên thể hiện sự phân tán giữa giá thực tế và giá dự đoán. Các điểm gần đường chéo lý tưởng 
        cho thấy mô hình dự đoán chính xác, trong khi các điểm lệch khỏi đường này chỉ ra sai số trong dự đoán.</p>
    </div>
    {% endif %}

    <table>
        <thead>
            <tr>
                <th>Hãng</th>
                <th>Model</th>
                <th>Năm sản xuất</th>
                <th>Quãng đường đã đi</th>
                <th>Loại nhiên liệu</th>
                <th>Động cơ</th>
                <th>Hộp số</th>
                <th>Màu ngoài</th>
                <th>Màu trong</th>
                <th>Tình trạng tai nạn</th>
                <th>Tiêu đề sạch</th>
                <th>Giá thực tế</th>
                <th>Giá dự đoán</th>
                <th>Giá chênh lệch</th>
            </tr>
        </thead>
        <tbody>
            {% for row in data %}
            <tr>
                <td>{{ row["brand"] }}</td>
                <td>{{ row["model"] }}</td>
                <td>{{ row["model_year"] }}</td>
                <td>{{ row["milage"] }}</td>
                <td>{{ row["fuel_type"] }}</td>
                <td>{{ row["engine"] }}</td>
                <td>{{ row["transmission"] }}</td>
                <td>{{ row["ext_col"] }}</td>
                <td>{{ row["int_col"] }}</td>
                <td>{{ row["accident"] }}</td>
                <td>{{ row["clean_title"] }}</td>
                <td>{{ row["price"] }}</td>
                <td>{{ row["predicted_price"] }}</td>
                <td>{{ row["price_difference"] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="pagination">
        {% if page > 1 %}
        <a href="{{ url_for('predict', filename=filename, page=page-1) }}">⬅️ Trang trước</a>
        {% endif %}
        <span>🎄 Trang {{ page }} / {{ total_pages }} 🎄</span>
        {% if page < total_pages %}
        <a href="{{ url_for('predict', filename=filename, page=page+1) }}">Trang sau ➡️</a>
        {% endif %}
    </div>

    <div class="page-input">
        <label for="page">Nhập số trang:</label>
        <input type="number" id="page" name="page" value="{{ page }}" min="1" max="{{ total_pages }}" 
        onkeydown="if(event.key === 'Enter'){ goToPage(); }">
    </div>

    <script>
        function goToPage() {
            const page = document.getElementById('page').value;
            if (page >= 1 && page <= {{ total_pages }}) {
                window.location.href = '{{ url_for("predict", filename=filename, page="") }}' + page;
            } else {
                alert("Số trang không hợp lệ. Vui lòng nhập số trang từ 1 đến " + {{ total_pages }});
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "Không tìm thấy file!"
    file = request.files["file"]
    if file.filename == "":
        return "Không có file nào được chọn!"
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return redirect(url_for("predict", filename=file.filename, page=1))


@app.route("/predict/<filename>")
def predict(filename):
    page = int(request.args.get("page", 1))
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Tạo đối tượng từ lớp DuDoanGiaXeOtoCu
    predictor = DuDoanGiaXeOtoCu(filepath)
    predictor.tai_du_lieu()
    
    if predictor.du_lieu is None:
        return "Không thể tải dữ liệu hoặc dữ liệu không hợp lệ."

    _, X_test, y_test = predictor.huan_luyen_mo_hinh()

    y_pred = predictor.mo_hinh_tot_nhat.predict(predictor.du_lieu[predictor.dac_trung])
    du_lieu_goc = predictor.du_lieu.copy()
    du_lieu_goc["predicted_price"] = y_pred
    du_lieu_goc["price_difference"] = (y_pred - du_lieu_goc["price"]).round(2)

    result_file = os.path.join(UPLOAD_FOLDER, "ket_qua_du_doan.csv")
    du_lieu_goc.to_csv(result_file, index=False)

    total_rows = len(du_lieu_goc)
    total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
    start_row = (page - 1) * ROWS_PER_PAGE
    end_row = start_row + ROWS_PER_PAGE
    data_preview = du_lieu_goc.iloc[start_row:end_row].to_dict(orient="records")

    # Tạo biểu đồ dự đoán giá ô tô
    fig, ax = plt.subplots(figsize=(10, 6))  # Kích thước biểu đồ

    ax.scatter(du_lieu_goc["price"], du_lieu_goc["predicted_price"], alpha=0.7, label="Dự đoán", color='blue')
    ax.plot([du_lieu_goc["price"].min(), du_lieu_goc["price"].max()],
            [du_lieu_goc["price"].min(), du_lieu_goc["price"].max()], 'r--', label="Đường lý tưởng")

    ax.set_xlabel("Giá thực tế", fontsize=12)
    ax.set_ylabel("Giá dự đoán", fontsize=12)
    ax.set_title("Giá thực tế vs Giá dự đoán", fontsize=14)
    ax.legend()

    # Lưu biểu đồ vào file hình ảnh với độ phân giải cao
    chart_path = os.path.join(UPLOAD_FOLDER, "chart.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close(fig)
    
    return render_template_string(RESULTS_HTML, data=data_preview, page=page, total_pages=total_pages, filename=filename, 
                                  file_url=url_for("download_file", filename="ket_qua_du_doan.csv"), chart_url=url_for("download_file", filename="chart.png"))

@app.route("/download/<filename>")
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
