from flask import Flask, render_template_string, request, redirect, url_for, send_file, flash
import pandas as pd
import os
import math
import plotly.express as px
import plotly.utils
import json
from doangiaxe import DuDoanGiaXeOtoCu
import doangiaxe  # Import lớp từ file doangiaxe.py


# Khởi tạo Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ROWS_PER_PAGE = 10  # Số dòng hiển thị mỗi trang

# Trang chủ
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
            background: #ffebcd;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #d9534f;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 20px;
            font-family: "Roboto", sans-serif;
        }
        .header {
            display: flex;
            justify-content: space-between;
            padding: 20px;
            background-color: #f39c12;
            color: white;
        }
        .header-left {
            font-size: 1.5em;
            font-family: "Roboto", sans-serif;
        }
        form {
            text-align: center;
            margin-top: 20px;
        }
        label {
            font-size: 1.2em;
            margin-right: 10px;
            font-family: "Roboto", sans-serif;
        }
        input[type="file"] {
            padding: 10px;
            font-size: 1em;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            font-size: 1.2em;
            background-color: #28a745;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        button:hover {
            background-color: #218838;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            font-size: 1em;
            color: #d9534f;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            Tên Nhóm: AIIA | HUTECH Đại Học Công Nghệ Thành Phố Hồ Chí Minh
        </div>
    </div>
    <h1>🎆 Dự Đoán Giá Xe Ô Tô Cũ 🎇</h1>
    <form action="/upload" method="post" enctype="multipart/form-data" style="text-align:center; margin-top: 20px;">
        <label for="file">🎁 Chọn file CSV:</label>
        <input type="file" name="file" id="file">
        <button type="submit">✨ Tải lên và Dự đoán ✨</button>
    </form>
    <div class="footer">
        <p>Chúc Mừng Năm Mới! 🧧🎉</p>
    </div>
</body>
</html>
"""

# Trang kết quả với biểu đồ và bảng dữ liệu
RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kết Quả Dự Đoán</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: "Arial", sans-serif;
            background: #fff5e6;
            color: #333;
            margin: 0;
            padding: 0;
        }
        h1 {
            text-align: center;
            color: #d9534f;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            background-color: #f39c12;
            color: white;
        }
        .header-left {
            font-size: 1.5em;
            font-family: "Roboto", sans-serif;
        }
        
        /* Hamburger Menu Styles */
        .menu-btn {
            font-size: 24px;
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 10px;
        }
        
        .dropdown {
            position: relative;
            display: inline-block;
        }
        
        .dropdown-content {
            display: none;
            position: absolute;
            right: 0;
            background-color: #f9f9f9;
            min-width: 200px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            z-index: 1;
            border-radius: 5px;
        }
        
        .dropdown-content a {
            color: black;
            padding: 12px 16px;
            text-decoration: none;
            display: block;
            transition: background-color 0.3s;
        }
        
        .dropdown-content a:hover {
            background-color: #f1f1f1;
        }
        
        .show {
            display: block;
        }
        
        table {
            margin: auto;
            border-collapse: collapse;
            width: 90%;
            background-color: rgba(255, 255, 255, 0.8);
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }
        th {
            background-color: #FF6347;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
        .plot-container {
            width: 95%;
            margin: auto;
        }
        .pagination {
            text-align: center;
            margin-top: 20px;
        }
        .pagination a {
            color: #FF6347;
            font-size: 1.2em;
            padding: 10px;
            text-decoration: none;
        }
        .pagination a:hover {
            background-color: #ddd;
        }
    </style>
    <script>
        function toggleMenu() {
            document.getElementById("myDropdown").classList.toggle("show");
        }
        
        window.onclick = function(event) {
            if (!event.target.matches('.menu-btn')) {
                var dropdowns = document.getElementsByClassName("dropdown-content");
                for (var i = 0; i < dropdowns.length; i++) {
                    var openDropdown = dropdowns[i];
                    if (openDropdown.classList.contains('show')) {
                        openDropdown.classList.remove('show');
                    }
                }
            }
        }
    </script>
</head>
<body>
    <div class="header">
        <div class="header-left">
            Tên Nhóm: AIIA | HUTECH Đại Học Công Nghệ Thành Phố Hồ Chí Minh
        </div>
        <div class="dropdown">
            <button onclick="toggleMenu()" class="menu-btn">☰</button>
            <div id="myDropdown" class="dropdown-content">
                <a href="{{ url_for('compare', filename=filename) }}">🔍 Xem mô hình so sánh</a>
                <a href="{{ file_url }}">🎁 Tải về kết quả đầy đủ</a>
                <a href="{{ url_for('index') }}">🏠 Về trang chủ</a>
            </div>
        </div>
    </div>
    <h1>🎁 Kết Quả Dự Đoán 🎁</h1>
    <div class="plot-container">
        <div id="chart"></div>
        <script>
            var chartData = {{ chart_data | safe }};
            Plotly.newPlot('chart', chartData.data, chartData.layout);
        </script>
    </div>
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
                <th>Giá hiện tại</th>
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
        <span>🌸🌸🌸 Trang {{ page }} / {{ total_pages }} 🌸🌸🌸</span>
        {% if page < total_pages %}
        <a href="{{ url_for('predict', filename=filename, page=page+1) }}">Trang sau ➡️</a>
        {% endif %}
        <form method="get" action="{{ url_for('predict', filename=filename) }}" style="margin-top: 10px;">
            <label for="page">Nhập số trang muốn đến:</label>
            <input type="number" id="page" name="page" min="1" max="{{ total_pages }}" value="{{ page }}">
            <button type="submit">Chuyển</button>
        </form>
    </div>
</body>
</html>
"""

# Trang so sánh mô hình (giữ nguyên như cũ)
COMPARE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>So Sánh Hiệu Suất Mô Hình</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: "Arial", sans-serif;
            background: #fff5e6;
            color: #333;
        }
        h1, h2 {
            text-align: center;
            color: #d9534f;
            font-weight: bold;
        }
        h1 { font-size: 2.5em; margin-bottom: 20px; }
        h2 { font-size: 1.8em; margin-top: 30px; }
        .header {
            display: flex;
            justify-content: space-between;
            padding: 20px;
            background-color: #f39c12;
            color: white;
        }
        .header-left {
            font-size: 1.5em;
            font-family: "Roboto", sans-serif;
        }
        .header-right {
            font-size: 1em;
            text-align: right;
        }
        table {
            margin: auto;
            border-collapse: collapse;
            width: 90%;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }
        th {
            background-color: #FF6347;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
        .plot-container {
            width: 90%;
            margin: auto;
            margin-top: 20px;
        }
        .total-score-table {
            background-color: #e6f2ff;
            border: 2px solid #4CAF50;
        }
        .total-score-table th {
            background-color: #4CAF50;
        }
        .total-score-header {
            color: #2196F3;
            text-align: center;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            Tên Nhóm: AIIA | HUTECH Đại Học Công Nghệ Thành Phố Hồ Chí Minh
        </div>
        <div class="header-right">
            <a href="{{ url_for('predict', filename=filename) }}" style="color: white; text-decoration: none;">↩️ Quay lại</a>
        </div>
    </div>
    <h1>So Sánh Hiệu Suất Các Mô Hình</h1>
    <div class="plot-container">
        <div id="chart"></div>
        <script>
            var chartData = {{ chart_data | safe }};
            Plotly.newPlot('chart', chartData.data, chartData.layout);
        </script>
    </div>
    <table>
        <thead>
            <tr>
                <th>Tên Mô Hình</th>
                <th>MSE</th>
                <th>RMSE</th>
                <th>R2</th>
                <th>MAE</th>
                <th>MAPE</th>
            </tr>
        </thead>
        <tbody>
            {% for model, metrics in models.items() %}
            <tr>
                <td>{{ model }}</td>
                <td>{{ metrics['MSE'] }}</td>
                <td>{{ metrics['RMSE'] }}</td>
                <td>{{ metrics['R2'] }}</td>
                <td>{{ metrics['MAE'] }}</td>
                <td>{{ metrics['MAPE'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2 class="total-score-header">🏆 Bảng Tổng Điểm Mô Hình 🏆</h2>
<table class="total-score-table">
    <thead>
        <tr>
            <th>Tên Mô Hình</th>
            <th>R2 Điểm (40%)</th>
            <th>MAPE Điểm (30%)</th>
            <th>RMSE Điểm (30%)</th>
            <th>Tổng Điểm</th>
        </tr>
    </thead>
    <tbody>
        {% for model, metrics in models.items() %}
        <tr>
            <td>{{ model }}</td>
            <td>{{ metrics['R2_Score'] }}</td>
            <td>{{ metrics['MAPE_Score'] }}</td>
            <td>{{ metrics['RMSE_Score'] }}</td>
            <td>{{ metrics['Total_Score'] }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

    <h2>Giới thiệu về các chỉ số hiệu suất</h2>
    <p>Để so sánh hiệu suất của các mô hình dự đoán, chúng ta sử dụng các chỉ số sau:</p>

    <ul>
        <li><strong>R2 (Coefficient of Determination):</strong> R2 là một chỉ số đo lường mức độ phù hợp của mô hình với dữ liệu thực tế. Giá trị R2 nằm trong khoảng từ 0 đến 1, với 1 là mô hình hoàn hảo. Chúng ta gán trọng số 0.4 cho R2, nghĩa là R2 sẽ đóng góp 40% vào tổng điểm của mỗi mô hình.</li>
        <li><strong>MAPE (Mean Absolute Percentage Error):</strong> MAPE là chỉ số đo lường sai số tương đối trung bình, tính bằng phần trăm. Giá trị MAPE càng thấp, mô hình càng chính xác. Chúng ta muốn tối đa hóa (1 - MAPE), vì vậy chúng ta sẽ nhân với trọng số 0.3, tương đương với 30% tổng điểm.</li>
        <li><strong>RMSE (Root Mean Squared Error):</strong> RMSE là căn bậc hai của MSE (Mean Squared Error), đo lường độ lệch trung bình của dự đoán so với giá trị thực tế. Giá trị RMSE càng thấp, mô hình càng chính xác. Chúng ta muốn tối đa hóa (1 - RMSE / y_test.std()), vì vậy chúng ta sẽ nhân với trọng số 0.3, tương đương với 30% tổng điểm.</li>
    </ul>

    <h2>Tóm tắt về các chỉ số hiệu suất</h2>
    <p>Bằng cách này, chúng ta sẽ tính tổng điểm cho mỗi mô hình, sử dụng sự kết hợp của ba chỉ số hiệu suất quan trọng (R2, MAPE và RMSE). Mô hình có tổng điểm cao nhất sẽ được chọn làm mô hình tốt nhất.</p>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("Không tìm thấy file!", "error")
        return redirect(url_for("index"))
    file = request.files["file"]
    if file.filename == "":
        flash("Không có file nào được chọn!", "error")
        return redirect(url_for("index"))
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return redirect(url_for("predict", filename=file.filename, page=1))

@app.route("/predict/<filename>", methods=["GET"])
def predict(filename):
    page = int(request.args.get("page", 1))
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        predictor = DuDoanGiaXeOtoCu(filepath)
        predictor.tai_du_lieu()
    except Exception as e:
        app.logger.error(f"Error loading data: {e}")
        flash("Không thể tải dữ liệu hoặc dữ liệu không hợp lệ.", "error")
        return redirect(url_for("index"))

    _, X_test, y_test = predictor.huan_luyen_mo_hinh()

    try:
        y_pred = predictor.mo_hinh_tot_nhat.predict(predictor.du_lieu[predictor.dac_trung])
        du_lieu_goc = predictor.du_lieu.copy()
        du_lieu_goc["predicted_price"] = y_pred
        du_lieu_goc["price_difference"] = (y_pred - du_lieu_goc["price"]).round(2)
    except Exception as e:
        app.logger.error(f"Error making predictions: {e}")
        flash("Đã xảy ra lỗi khi dự đoán giá.", "error")
        return redirect(url_for("index"))

    du_lieu_goc["price"] = du_lieu_goc["price"].apply(lambda x: f"${x:,.2f}")
    du_lieu_goc["predicted_price"] = du_lieu_goc["predicted_price"].apply(lambda x: f"${x:,.2f}")
    du_lieu_goc["price_difference"] = du_lieu_goc["price_difference"].apply(lambda x: f"${x:,.2f}")

    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_predicted = request.args.get("min_predicted", type=int)
    max_predicted = request.args.get("max_predicted", type=int)

    if min_price:
        du_lieu_goc = du_lieu_goc[du_lieu_goc["price"].str.replace(",", "").str.extract(r'(\d+)', expand=False).astype(int) >= min_price]
    if max_price:
        du_lieu_goc = du_lieu_goc[du_lieu_goc["price"].str.replace(",", "").str.extract(r'(\d+)', expand=False).astype(int) <= max_price]
    if min_predicted:
        du_lieu_goc = du_lieu_goc[du_lieu_goc["predicted_price"].str.replace(",", "").str.extract(r'(\d+)', expand=False).astype(int) >= min_predicted]
    if max_predicted:
        du_lieu_goc = du_lieu_goc[du_lieu_goc["predicted_price"].str.replace(",", "").str.extract(r'(\d+)', expand=False).astype(int) <= max_predicted]

    total_rows = len(du_lieu_goc)
    total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
    start_row = (page - 1) * ROWS_PER_PAGE
    end_row = start_row + ROWS_PER_PAGE
    data_preview = du_lieu_goc.iloc[start_row:end_row]

    try:
        fig = px.scatter(
            data_preview,
            x="price",
            y="predicted_price",
            color="brand",
            hover_data=["model", "model_year", "price", "predicted_price", "price_difference"],
            title="Giá hiện tại vs Giá dự đoán (Trang {})".format(page)
        )

        fig.update_layout(xaxis_title="Giá hiện tại ($)", yaxis_title="Giá dự đoán ($)", legend_title="Hãng xe")

        chart_data = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        app.logger.error(f"Error generating chart: {e}")
        flash("Đã xảy ra lỗi khi hiển thị biểu đồ.", "error")
        chart_data = None

    return render_template_string(RESULTS_HTML, 
                                data=data_preview.to_dict(orient="records"),
                                page=page, 
                                total_pages=total_pages, 
                                filename=filename, 
                                file_url=url_for("download_file", filename="ket_qua_du_doan.csv"),
                                chart_data=chart_data,
                                min_price=min_price,
                                max_price=max_price,
                                min_predicted=min_predicted,
                                max_predicted=max_predicted)


def calculate_model_scores(models_metrics, y_test):
    scored_models = {}
    for model_name, metrics in models_metrics.items():
        r2_score = metrics['R2']
        mape_score = 1 - metrics['MAPE']
        rmse_score = 1 - metrics['RMSE'] / y_test.std()

        total_score = r2_score * 0.4 + mape_score * 0.3 + rmse_score * 0.3
        scored_models[model_name] = {
            'R2_Score': round(r2_score * 100, 2),
            'MAPE_Score': round(mape_score * 100, 2),
            'RMSE_Score': round(rmse_score * 100, 2),
            'Total_Score': round(total_score * 100, 2)
        }
    return scored_models

def generate_model_comparison_plot(models_metrics):
    """
    Tạo biểu đồ so sánh hiệu suất các mô hình
    """
    import plotly.graph_objs as go
    
    # Chuẩn bị dữ liệu cho biểu đồ
    models = list(models_metrics.keys())
    r2_values = [metrics['R2'] for metrics in models_metrics.values()]
    mape_values = [metrics['MAPE'] for metrics in models_metrics.values()]
    rmse_values = [metrics['RMSE'] for metrics in models_metrics.values()]
    total_scores = [metrics['Total_Score'] for metrics in models_metrics.values()]
    
    # Tạo biểu đồ so sánh đa chỉ số
    fig = go.Figure(data=[
        go.Bar(name='R2', x=models, y=r2_values),
        go.Bar(name='MAPE', x=models, y=mape_values),
        go.Bar(name='RMSE', x=models, y=rmse_values),
        go.Scatter(
            name='Tổng Điểm', 
            x=models, 
            y=total_scores, 
            mode='lines+markers',
            line=dict(color='red', width=2),
            marker=dict(size=10)
        )
    ])
    
    # Cấu hình layout
    fig.update_layout(
        title='So Sánh Hiệu Suất Các Mô Hình',
        xaxis_title='Mô Hình',
        yaxis_title='Giá Trị',
        barmode='group'
    )
    
    # Chuyển biểu đồ sang dạng JSON để render
    return json.loads(fig.to_json())

from doangiaxe import DuDoanGiaXeOtoCu

@app.route('/compare', methods=['POST'])
def compare_models():
    duong_dan_du_lieu = request.form['duong_dan_du_lieu']
    he_thong = DuDoanGiaXeOtoCu(duong_dan_du_lieu)
    he_thong.tai_du_lieu()
    ket_qua, X_test, y_test = he_thong.huan_luyen_mo_hinh()

    # Tính điểm số và trả về cho template
    scored_models = calculate_model_scores(ket_qua)
    chart_data = generate_model_comparison_plot(scored_models)

    return render_template_string(
        COMPARE_HTML, 
        models=scored_models, 
        chart_data=chart_data,
        filename=request.form.get('filename', '')
    )

@app.route("/compare/<filename>")
def compare(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        predictor = DuDoanGiaXeOtoCu(filepath)
        predictor.tai_du_lieu()
        results, _, _ = predictor.huan_luyen_mo_hinh()
    except Exception as e:
        app.logger.error(f"Error loading data or training models: {e}")
        flash("Không thể tải dữ liệu hoặc huấn luyện mô hình.", "error")
        return redirect(url_for("index"))

    try:
        model_names = list(results.keys())
        metrics = ['MSE', 'RMSE', 'R2', 'MAE', 'MAPE']
        data = {
            metric: [results[model][metric] for model in model_names] for metric in metrics
        }

        fig = px.bar(
            pd.DataFrame(data, index=model_names).reset_index().melt(id_vars=['index'], var_name='Metric', value_name='Value'),
            x='index', y='Value', color='Metric',
            title="So Sánh Hiệu Suất Mô Hình",
            labels={'index': 'Tên Mô Hình'}
        )

        fig.update_layout(xaxis_title="Mô Hình", yaxis_title="Giá Trị", legend_title="Chỉ Số")

        chart_data = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        app.logger.error(f"Error generating comparison chart: {e}")
        flash("Đã xảy ra lỗi khi hiển thị so sánh mô hình.", "error")
        chart_data = None

    return render_template_string(COMPARE_HTML, models=results, chart_data=chart_data, filename=filename)

@app.route("/download/<filename>")
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(filepath, as_attachment=True)

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal Server Error: {error}")
    flash("Đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại sau.", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=False)