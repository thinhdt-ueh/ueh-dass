# DASS

**UEH Data Analysis for Social Sciences** — ứng dụng web phân tích thống kê tương tự SPSS, viết bằng Python (Streamlit).

## Cài đặt

```bash
cd UEH-DASS
pip install -r requirements.txt
```

## Chạy ứng dụng

```bash
streamlit run app.py
```

Trình duyệt sẽ tự mở tại `http://localhost:8501`.

## Chạy bằng Docker

```bash
docker compose up --build
```

Ứng dụng sẽ chạy tại `http://localhost:8501`. Dùng `docker compose up -d --build` để chạy nền, và `docker compose down` để dừng.

## Chạy bằng file .exe (Windows)

File `DASS.exe` (có sẵn trong repo, thư mục gốc) là launcher tự chạy: bấm đúp để tự khởi động máy chủ Streamlit và tự mở trình duyệt tại `http://localhost:8501`, không cần mở terminal hay gõ lệnh.

**Portable — dùng được trên bất kỳ máy Windows nào**, không phụ thuộc đường dẫn hay `.venv` có sẵn: cần tải về **cả thư mục dự án** (không chỉ riêng file `.exe`), giữ `DASS.exe` cùng cấp với `app.py`/`requirements.txt`. Lần chạy đầu tiên, nếu chưa có môi trường Python sẵn sàng, launcher sẽ tự tạo `.venv` mới và tự cài các thư viện cần thiết (cần máy đã cài sẵn Python 3.10+ và có kết nối Internet) — quá trình này mất vài phút; các lần chạy sau sẽ khởi động ngay lập tức. Đóng cửa sổ console (hoặc Ctrl+C) để dừng ứng dụng.

Muốn tự build lại `DASS.exe` từ source:

```bash
pip install pyinstaller
pyinstaller --onefile --console --name DASS --icon assets/logo-ueh.ico launcher.py
```

File build ra nằm trong thư mục `dist/`, copy ra thư mục gốc của dự án để dùng.

## Bắt đầu

1. Ở thanh bên trái (sidebar), chọn ngôn ngữ (mặc định English, có thể đổi sang Tiếng Việt), rồi import dữ liệu của bạn (CSV / Excel / SPSS `.sav`), hoặc bấm **"Use sample data (demo)"** để khám phá ngay các chức năng với một bộ dữ liệu khảo sát mẫu (n=200, tự động bằng đúng ngôn ngữ đang chọn).
2. Dùng menu điều hướng để chuyển giữa các module:
   - **Data Management**: Recode (mã hóa / đảo điểm), xử lý dữ liệu khuyết, tính biến mới (Compute)
   - **Descriptive Statistics**: Frequencies, Descriptives, Crosstabs (kèm Cramér's V/Phi), Chi-square Goodness-of-Fit
   - **Scale Evaluation**: Cronbach's Alpha, EFA
   - **Hypothesis Testing**: Independent/Paired T-test (kèm Cohen's d & khoảng tin cậy 95%), One-Way ANOVA (kèm eta²/omega²), Two-Way ANOVA
   - **Relational Analysis**: Pearson Correlation, Hồi quy tuyến tính/đa biến
   - **Non-parametric & Graphs**: Shapiro-Wilk, Mann-Whitney U, Kruskal-Wallis, Wilcoxon, Histogram/Scatter/Boxplot/Bar chart
3. Ở mỗi phân tích có ô **"➕ Add results to the report when run"** — tick trước khi chạy để kết quả (bảng + diễn giải) được gom vào báo cáo, rồi tải về file **Word (.docx)** ở mục "📄 Analysis Report" trong sidebar.
4. Mục **"📤 Export Data"** ở sidebar tải về CSV/Excel của bộ dữ liệu hiện tại — bao gồm mọi biến đã Recode/Compute/xử lý khuyết, và mọi chỉnh sửa trực tiếp trong Data View (tự động lưu, không cần bấm nút riêng).
5. Mục **"💾 Project"** ở sidebar cho lưu toàn bộ phiên làm việc (dữ liệu + nhãn biến + nhật ký xử lý + báo cáo đang gom) thành 1 file `.json` duy nhất, và mở lại sau bằng nút "Open project".

## Đa ngôn ngữ (i18n)

Toàn bộ giao diện (nhãn, nút bấm, tiêu đề trang, thông báo kết quả) hỗ trợ song ngữ Việt/Anh thông qua `utils/i18n.py`. Chuyển ngôn ngữ ở dropdown 🌐 đầu sidebar — áp dụng ngay lập tức trên toàn bộ ứng dụng, kể cả tên các trang trong menu điều hướng và cả bộ dữ liệu mẫu. Nội dung do người dùng nhập/đặt tên (tên biến, nhãn, giá trị dữ liệu thật) không bị dịch.

## Kiểm thử (Testing)

```bash
pip install -r requirements-dev.txt
pytest
```

Bộ test (`tests/`) gồm: kiểm tra khớp key song ngữ VI/EN, unit test cho các hàm thống kê (`utils/stats.py`), smoke test mọi trang (có/không có dữ liệu), và test riêng cho CFA (fit tốt/xấu, 1 nhân tố, lỗi validate, ước lượng DWLS+Polychoric, xuất Word).

## Cấu trúc dự án

```
UEH-DASS/
├── app.py                              # st.navigation, sidebar dùng chung (ngôn ngữ, import/export, project, report), trang chủ
├── footer.html                         # Footer nhúng ở cuối mọi trang — sửa trực tiếp file này
├── requirements.txt
├── assets/
│   └── logo-ueh.png                    # Logo UEH, hiển thị đầu sidebar qua st.logo()
├── utils/
│   ├── state.py                        # Quản lý session_state (dữ liệu, nhãn biến, log, ngôn ngữ)
│   ├── stats.py                        # Hàm thống kê dùng chung (Cronbach's Alpha, Cohen's d, eta²/omega², ...)
│   ├── i18n.py                         # Từ điển Việt/Anh + hàm t()
│   ├── export.py                       # Xuất dữ liệu hiện tại ra CSV/Excel (bytes)
│   ├── project.py                      # Lưu/mở phiên làm việc (.json)
│   ├── report.py                       # Gom kết quả phân tích + xuất báo cáo Word (.docx)
│   └── footer.py                       # Render footer.html ở cuối mỗi trang
└── pages/
    ├── 1_🔧_Bien_doi_du_lieu.py         # Data Management
    ├── 2_📊_Thong_ke_mo_ta.py           # Descriptive Statistics
    ├── 3_✅_Danh_gia_thang_do.py        # Scale Evaluation
    ├── 4_🧪_Kiem_dinh_gia_thuyet.py     # Hypothesis Testing
    ├── 5_📈_Phan_tich_tuong_quan.py     # Relational Analysis
    └── 6_🧮_Phi_tham_so_Bieu_do.py      # Non-parametric & Graphs
```

Dữ liệu được lưu trong `st.session_state` trong suốt phiên làm việc — mọi biến đổi (recode, compute, xử lý khuyết, sửa trực tiếp trong Data View...) áp dụng ngay lên bộ dữ liệu và có thể dùng tiếp ở các module phân tích khác, hoặc xuất ra file ở sidebar. Nhật ký các thao tác biến đổi được ghi lại và có thể xem ở cuối mỗi trang.
