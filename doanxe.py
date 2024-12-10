import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, mean_absolute_percentage_error
import joblib
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


class DuDoanGiaXeOtoCu:
    def __init__(self, duong_dan_du_lieu):
        self.duong_dan_du_lieu = duong_dan_du_lieu
        self.du_lieu = None
        self.dac_trung = None
        self.bo_ma_hoa_nhan = {}
        self.mo_hinh_tot_nhat = None
        self.index_test = None

    def tai_du_lieu(self):
        try:
            self.du_lieu = pd.read_csv(self.duong_dan_du_lieu)

            # Làm sạch dữ liệu
            self.du_lieu['milage'] = pd.to_numeric(
                self.du_lieu['milage'].str.replace(r'[^\d.]', '', regex=True), errors='coerce'
            )
            self.du_lieu['price'] = pd.to_numeric(
                self.du_lieu['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce'
            )

            self.du_lieu['accident'] = self.du_lieu['accident'].fillna('None reported')
            self.du_lieu['clean_title'] = self.du_lieu['clean_title'].fillna('Unknown')

            self.du_lieu = self.du_lieu.dropna(subset=['milage', 'price', 'model_year'])

            if self.du_lieu.empty:
                raise ValueError("Dữ liệu trống sau khi làm sạch.")

            dac_trung_phan_loai = ['brand', 'model', 'fuel_type', 'engine', 'transmission', 'ext_col', 'int_col']
            for dac_trung in dac_trung_phan_loai:
                encoder = LabelEncoder()
                self.du_lieu[dac_trung + '_encoded'] = encoder.fit_transform(self.du_lieu[dac_trung].astype(str))
                self.bo_ma_hoa_nhan[dac_trung] = encoder

            self.du_lieu['tuoi_xe'] = datetime.now().year - self.du_lieu['model_year']
            self.du_lieu['km_moi_nam'] = (self.du_lieu['milage'] / (self.du_lieu['tuoi_xe'] + 1)).clip(0)

            self.dac_trung = [
                'model_year', 'milage', 'tuoi_xe', 'km_moi_nam',
                'brand_encoded', 'model_encoded', 'fuel_type_encoded',
                'engine_encoded', 'transmission_encoded', 'ext_col_encoded', 'int_col_encoded'
            ]
        except Exception as e:
            print(f"Lỗi tải dữ liệu: {e}")
            self.du_lieu = None

    def tien_xu_ly_du_lieu(self, test_size=0.2):
        if self.du_lieu is None or self.dac_trung is None:
            raise ValueError("Dữ liệu chưa được tải hoặc xử lý.")

        X = self.du_lieu[self.dac_trung]
        y = self.du_lieu['price']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        self.index_test = X_test.index

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        return X_train_scaled, X_test_scaled, y_train, y_test

    def huan_luyen_mo_hinh(self):
        X_train, X_test, y_train, y_test = self.tien_xu_ly_du_lieu()

        cac_mo_hinh = {
            'Hồi Quy Tuyến Tính': LinearRegression(),
            'Ridge Regression': Ridge(alpha=1.0),
            'Lasso Regression': Lasso(alpha=1.0),
            'Rừng Ngẫu Nhiên': RandomForestRegressor(n_estimators=200, random_state=42),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=200, random_state=42),
        }

        ket_qua_mo_hinh = {}
        for ten, mo_hinh in cac_mo_hinh.items():
            mo_hinh.fit(X_train, y_train)
            y_du_doan = mo_hinh.predict(X_test)

            ket_qua_mo_hinh[ten] = {
                'MSE': mean_squared_error(y_test, y_du_doan),
                'RMSE': np.sqrt(mean_squared_error(y_test, y_du_doan)),
                'R2': r2_score(y_test, y_du_doan),
                'MAE': mean_absolute_error(y_test, y_du_doan),
                'MAPE': mean_absolute_percentage_error(y_test, y_du_doan)
            }

        self.mo_hinh_tot_nhat = max(
            cac_mo_hinh.items(), key=lambda x: ket_qua_mo_hinh[x[0]]['R2']
        )[1]

        return ket_qua_mo_hinh, X_test, y_test

    def luu_ket_qua_vao_file(self, X_test, y_test, file_name="ket_qua_du_doan.csv"):
        if self.mo_hinh_tot_nhat is None:
            raise ValueError("Chưa có mô hình để lưu kết quả.")
        
        # Dự đoán cho toàn bộ dữ liệu, không chỉ X_test
        X_full = self.du_lieu[self.dac_trung]  # Toàn bộ dữ liệu mà bạn đã chọn đặc trưng
        y_pred = self.mo_hinh_tot_nhat.predict(X_full)
        
        # Tạo DataFrame kết quả cho toàn bộ dữ liệu
        thong_tin_xe = self.du_lieu[['brand', 'model', 'model_year', 'milage', 'fuel_type', 'engine', 
                                      'transmission', 'ext_col', 'int_col', 'accident', 'clean_title', 'price']]
        
        # Tạo DataFrame kết quả
        ket_qua_df = thong_tin_xe.copy()
        ket_qua_df['Giá dự đoán'] = y_pred
        ket_qua_df['Giá chênh lệch'] = y_pred - self.du_lieu['price']

        # Định dạng lại dữ liệu cho dễ đọc
        ket_qua_df['milage'] = ket_qua_df['milage'].apply(lambda x: f"{x:,.0f} km")
        ket_qua_df['price'] = ket_qua_df['price'].apply(lambda x: f"${x:,.2f}")
        ket_qua_df['Giá dự đoán'] = ket_qua_df['Giá dự đoán'].apply(lambda x: f"${x:,.2f}")
        ket_qua_df['Giá chênh lệch'] = ket_qua_df['Giá chênh lệch'].apply(lambda x: f"${x:,.2f}")

        1

        # Lưu kết quả vào file CSV
        ket_qua_df.to_csv(file_name, index=False, encoding='utf-8-sig')  # Đảm bảo mã hóa UTF-8
        print(f"Kết quả đã được lưu vào file: {file_name}")

    def visualize_results(self, X_test, y_test):
        if self.mo_hinh_tot_nhat is None:
            raise ValueError("Chưa có mô hình để trực quan hóa.")

        y_pred = self.mo_hinh_tot_nhat.predict(X_test)

        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.7, label="Dự đoán")
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', label="Đường lý tưởng")
        plt.title("Giá hiện tại vs Giá dự đoán")
        plt.xlabel("Giá hiện tại")
        plt.ylabel("Giá dự đoán")
        plt.legend()
        plt.grid(alpha=0.5)
        plt.savefig("ket_qua_du_doan.png")
        print("Đã lưu đồ thị vào file 'ket_qua_du_doan.png'.")

    def luu_mo_hinh(self, ten_file='mo_hinh_du_doan_xe.pkl'):
        if self.mo_hinh_tot_nhat:
            joblib.dump(self.mo_hinh_tot_nhat, ten_file)
            print(f"Đã lưu mô hình vào {ten_file}")


if __name__ == "__main__":
    duong_dan_du_lieu = input("Nhập đường dẫn tới file dữ liệu: ")
    he_thong = DuDoanGiaXeOtoCu(duong_dan_du_lieu)
    he_thong.tai_du_lieu()

    if he_thong.du_lieu is not None:
        ket_qua, X_test, y_test = he_thong.huan_luyen_mo_hinh()

        print("\nHiệu suất các mô hình:")
        for ten, chi_so in ket_qua.items():
            print(f"\n{ten}:")
            for ten_chi_so, gia_tri in chi_so.items():
                print(f"  {ten_chi_so}: {gia_tri:.4f}")

        he_thong.visualize_results(X_test, y_test)
        he_thong.luu_mo_hinh()
        he_thong.luu_ket_qua_vao_file(X_test, y_test)
