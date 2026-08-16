# DASS — Claude Handover

Tài liệu bàn giao trạng thái dự án, để phiên làm việc sau (người hoặc Claude) tiếp tục mà không phải hỏi lại từ đầu. Cập nhật lần cuối: 2026-08-16 (phiên 2).

## Dự án là gì

**DASS — UEH Data Analysis for Social Sciences**: web app phân tích thống kê kiểu SPSS, viết bằng Python + Streamlit. Repo GitHub: **https://github.com/thinhdt-ueh/ueh-dass** (public, chủ tài khoản `thinhdt-ueh`).

Thư mục dự án trên máy: `C:\Users\thinhdt\UEH-DASS`.

## Quyết định đã chốt

- **Tên app**: "DASS", tagline "UEH Data Analysis for Social Sciences" (đổi từ "UEH-DASS" / "UEH Data Analysis Statistical Software" ban đầu theo yêu cầu user).
- **Ngôn ngữ mặc định của UI**: English (`DEFAULT_LANG = "en"` trong `utils/i18n.py`). Có song ngữ Việt/Anh đầy đủ qua `t()`, kể cả bộ dữ liệu mẫu.
- **Điều hướng**: dùng `st.navigation()` + `st.Page()` tường minh (không dùng auto-detect `pages/` cũ của Streamlit).
- **Report/Project**: gom kết quả phân tích vào báo cáo bằng **checkbox** (không dùng nút "➕ Add to report" lồng trong nút Run khác — xem mục Gotcha bên dưới), xuất Word (`.docx`). Lưu/mở phiên làm việc qua file `.json` tự chế (`utils/project.py`).
- **Deploy button** của Streamlit: ẩn qua `.streamlit/config.toml` (`toolbarMode = "minimal"`), không hack CSS.
- **Docker**: có `Dockerfile` + `docker-compose.yml`, chạy bằng `docker compose up --build`. Chưa test build thật trên máy này (máy không có Docker cài sẵn) — chỉ verify bằng đọc kỹ Dockerfile, chưa build/run thử.
- **File `.exe` tự chạy trên Windows**: `DASS.exe` (launcher, build bằng PyInstaller từ `launcher.py`) **có commit thẳng vào repo** (~7.9MB) theo yêu cầu rõ ràng của user ("đưa hết lên luôn nhé") — quyết định có hỏi lại user giữa 2 lựa chọn (GitHub Release vs commit thẳng vào repo, vì `gh release create` bị permission-classifier chặn), user chọn **commit thẳng vào repo**.
- **`.venv` không đưa vào git** (đúng chuẩn, venv chứa đường dẫn tuyệt đối máy-cụ-thể, không portable).
- Không đưa `playwright` vào `requirements.txt` — nó chỉ là công cụ dev/test, không phải dependency runtime của app.

## Trạng thái hiện tại (đã xong, đã test)

1. **App core**: đủ 6 nhóm chức năng gốc (Data Management, Descriptive Stats, Scale Evaluation, Hypothesis Testing, Correlation/Regression, Non-parametric & Graphs) + Two-Way ANOVA, Chi-square GOF, Cramér's V/Phi, effect sizes (Cohen's d/dz, eta²/omega²) + CI, Word report export, project save/load, User Guide song ngữ (`pages/7_❓_Huong_dan.py`).
2. **i18n**: 347 key, cross-check đủ VI/EN.
3. **GitHub**: repo `ueh-dass` public đã tạo và push đầy đủ (auth qua `gh` CLI, browser device-code login, tài khoản `thinhdt-ueh`).
4. **Docker**: `Dockerfile` (python:3.11-slim, cài `build-essential`+`curl`, healthcheck `/_stcore/health`) + `docker-compose.yml` (service `dass`, cổng `8501:8501`) — đã commit, đã push. **Chưa build/run thử thật** (không có Docker trên máy dev).
5. **`DASS.exe` launcher** (`launcher.py`, build bằng PyInstaller `--onefile --console --icon assets/logo-ueh.ico`):
   - Tự khởi động Streamlit server + tự mở trình duyệt tại `http://localhost:8501`.
   - **Portable**: không giả định `.venv` có sẵn nữa. Lần chạy đầu, nếu chưa có `.venv` hoạt động được cạnh file exe, tự tạo venv mới + `pip install -r requirements.txt`. Đã verify bằng cách copy cả project (trừ `.venv`) sang thư mục khác và chạy exe từ đó — tự dựng venv, cài xong, server lên, HTTP 200.
   - **Bỏ qua Python bản Microsoft Store** khi tìm system Python (`is_windows_store_python()` — check path chứa `WindowsApps`), vì venv tạo từ Python Store không đáng tin (lỗi đã gặp thật: `did not find executable at ...WindowsApps\PythonSoftwareFoundation.Python.3.13_.../python.exe`). Nếu không tìm được Python "thật" nào, launcher thoát sạch với thông báo rõ ràng hướng dẫn cài Python từ python.org, thay vì crash traceback.
   - Đã test cả 2 case bằng exe đã compile thật (không chỉ script nguồn): (a) máy có `.venv` sẵn — chạy ngay; (b) máy/thư mục mới không có Python thật (chỉ có Store Python, đúng như máy user báo lỗi) — báo lỗi thân thiện, không crash.

## Cập nhật 2026-08-16: thêm CFA (Confirmatory Factor Analysis)

Thêm tab thứ 3 vào `pages/3_✅_Danh_gia_thang_do.py` (cùng file với Cronbach's Alpha, EFA), dùng thư viện **`semopy`** (pure Python, không cần R/lavaan) — đã thêm `semopy>=2.3` vào `requirements.txt`.

- UI: chọn số nhân tố, đặt tên + chọn items cho từng nhân tố (>=2 items/nhân tố), nút Run, checkbox add-to-report theo đúng pattern cũ.
- Kết quả: model spec (cú pháp `F1 =~ X1 + X2 + ...`), bảng chỉ số phù hợp mô hình (χ², df, CFI, TLI, RMSEA, GFI, AGFI, NFI, AIC, BIC) kèm badge diễn giải, bảng hệ số tải chuẩn hóa (tô đậm ≥0.5), **Composite Reliability (CR) & AVE** per factor (hàm `cr_ave()` mới trong `utils/stats.py`), ma trận tương quan giữa các nhân tố + **Fornell–Larcker discriminant validity check** khi ≥2 nhân tố.
- 45 key i18n mới (`sc.cfa.*`), đã cross-check VI/EN khớp 1-1.
- **Gotcha đã gặp và fix**: `semopy.Model.inspect(std_est=True)` trả về cột `Std. Err`/`z-value`/`p-value` là **object dtype trộn lẫn float và chuỗi `"-"`** (marker cho reference-indicator bị fix = 1.0) — đưa thẳng vào `st.dataframe()` sẽ vỡ Arrow serialization (`ArrowTypeError`). Fix: format toàn bộ cột số thành string trước khi hiển thị/xuất báo cáo (xem hàm `_fmt` trong tab CFA).
- Đã test kỹ bằng `AppTest`: dữ liệu tương quan tốt (fit indices ra đúng ngưỡng "tốt"), dữ liệu random/không có cấu trúc (fit indices ra đúng ngưỡng "kém", kể cả case CFI/TLI âm — hợp lệ về mặt toán học khi model quá tệ), case 1 nhân tố (bỏ qua phần ma trận tương quan), case validate lỗi (factor thiếu item). Đã verify `build_docx_bytes()` xuất Word thành công với đủ 4 bảng.
- **Chưa test**: `DASS.exe` chưa được rebuild/test lại với `semopy` trong self-provisioning venv (không cần rebuild exe vì `requirements.txt` được đọc runtime, nhưng nếu user đã có `.venv` cũ từ trước sẽ không tự có `semopy` — cần xóa `.venv` hoặc tự `pip install semopy` thủ công để dùng tab CFA).

## Cập nhật 2026-08-16 (phiên 2): DWLS estimator cho CFA + test suite persisted

Sau khi thêm CFA (xem mục trên), user hỏi "còn nên sửa gì nữa" — đề xuất 3 việc, user đồng ý làm cả 3:

1. **DWLS + Polychoric estimator cho CFA** (mục `sc.cfa.estimator_*` trong CFA tab) — vì dữ liệu khảo sát Likert là ordinal, ML thuần không lý tưởng bằng WLSMV/DWLS. Phát hiện **2 lỗi tương thích ngược thật sự** trong `semopy 2.3.11` với numpy/scipy hiện tại (xem Gotcha #6 bên dưới) — đã tự viết workaround (`polychoric_cov()` + monkeypatch `bivariate_cdf` trong `pages/3_✅_Danh_gia_thang_do.py`), verify bằng cách so sánh polychoric vs Pearson correlation (polychoric phải luôn ≥ Pearson về độ lớn — đúng như lý thuyết) trước khi tích hợp vào UI.
2. **Test suite `pytest` persisted trong `tests/`** — 49 test, tất cả pass: `test_i18n.py` (VI/EN parity + duplicate-key check, thay thế script ad-hoc trước đây), `test_stats.py` (unit test các hàm trong `utils/stats.py`), `test_pages_smoke.py` (mọi trang load được, có/không có data), `test_cfa.py` (fit tốt, 1 nhân tố, validate lỗi, Arrow-safety, DWLS, xuất docx), `test_report.py` (build_docx_bytes với text/table/image block). Chạy bằng `pip install -r requirements-dev.txt && pytest`. `pytest.ini` dùng `pythonpath = .` để import `utils.*` không cần hack `sys.path`.
3. **Docker vẫn CHƯA build/run thử thật** — máy dev này (và có thể máy user) **không có Docker cài sẵn** (`docker --version` → not found). Cài Docker Desktop trên Windows là việc nặng (cần WSL2/Hyper-V, quyền admin, khả năng phải reboot) nên **không tự ý cài** — nếu user muốn verify Docker, cần họ tự cài hoặc xác nhận cho phép cài.

## Việc còn dở / chưa test hết

- **Docker chưa được build/run thử thật** trên bất kỳ máy nào — không có Docker trên máy dev để test, và việc cài Docker Desktop là thay đổi hệ thống nặng nên chưa tự ý làm. Nếu build thật gặp lỗi (khả nghi nhất: `pyreadstat` cần compile trên slim image dù đã cài `build-essential`), cần fix.
- **`DASS.exe` chưa được user tự tay double-click chạy sau bản fix Store-Python** (`fdf9a12`) — mới chỉ verify bằng cách tôi tự copy project sang thư mục test và chạy exe qua Bash tool, chưa có xác nhận trực tiếp từ user rằng máy Desktop của họ (nơi báo lỗi) đã chạy được sau khi cài Python thật từ python.org.
- Repo hiện có các file `.zip` lớn (~300MB) nằm trong thư mục dự án nhưng **không được track bởi git** (tên đổi qua vài lần: `UEH-DASS.zip` → `utils.zip` → `UEH-DASS_src.zip`, nhiều khả năng là user tự backup/zip thủ công qua File Explorer). Không đụng vào các file này, chỉ note lại để biết chúng không phải rác do Claude tạo ra.
- Chưa có ai yêu cầu thêm tính năng gì mới ngoài các mục ở trên tính đến thời điểm viết tài liệu này.

## Gotcha kỹ thuật quan trọng (để không lặp lại lỗi cũ)

1. **Nút lồng trong nút** (`if st.button(...):` chứa thêm `st.button()` bên trong) **không bao giờ bắn sự kiện click** ở lần rerun do nút trong gây ra — Streamlit chỉ báo "vừa được click" cho đúng 1 nút mỗi lần rerun. Đã fix bằng cách chuyển hết các nút "➕ Add to report" lồng bên trong nút Run thành **checkbox khai báo trước nút Run**.
2. **`st.file_uploader()` trả về cùng 1 `UploadedFile` object ở mọi lần rerun tiếp theo**, kể cả rerun do thao tác không liên quan ở nơi khác trong app (vì `render_sidebar()` chạy lại ở mọi tương tác). Phải guard bằng `uploaded.file_id` lưu trong `session_state`, chỉ xử lý khi id đổi — nếu không sẽ ghi đè âm thầm dữ liệu đã sửa.
3. **`AppTest.session_state.get(...)` không tồn tại** (raises AttributeError) — phải dùng `at.session_state["key"]` + try/except.
4. **Python bản Microsoft Store không đáng tin cho việc tạo `venv`** trên Windows — xem mục launcher ở trên. Luôn ưu tiên `py -3` / Python cài từ python.org, loại trừ mọi path chứa `WindowsApps`.
5. **`gh release create` bị chặn bởi permission classifier** của môi trường agent này — nếu cần publish release trong tương lai, phải hỏi user xác nhận trực tiếp hoặc dùng cách commit file thẳng vào repo thay thế.
6. **`semopy 2.3.11` có 2 lỗi tương thích ngược thật với numpy/scipy mới**: (a) `semopy.polycorr.hetcor()` transpose 1 DataFrame rồi index kiểu cột thay vì kiểu hàng (`data[v]` sau `data = data.T`) → `KeyError` khi truyền `ords` là tên cột thay vì index số; (b) `semopy.polycorr.bivariate_cdf()` gọi `scipy.stats.mvn.mvnun` — API này đã bị scipy xóa hẳn. Cả 2 đều KHÔNG do cách gọi sai của mình — đã verify bằng cách đọc source code trực tiếp. Workaround: tự viết `polychoric_cov()` (bỏ qua `hetcor`, tự loop `polychoric_corr()` từng cặp biến) + monkeypatch `bivariate_cdf` bằng `scipy.stats.multivariate_normal` (toán học tương đương, chỉ đổi API). Xem `pages/3_✅_Danh_gia_thang_do.py`. Cũng phát hiện: `model.fit(cov=..., obj='DWLS')` một mình báo lỗi `'Model' object has no attribute 'mx_data'` — DWLS cần CẢ `data=` lẫn `cov=` cùng lúc (`data` để tính ma trận trọng số tiệm cận, `cov` để làm ma trận mục tiêu).

## Cấu trúc file chính

```
UEH-DASS/
├── app.py                  # entry point, st.navigation, sidebar dùng chung
├── launcher.py             # source của DASS.exe (self-provisioning venv)
├── DASS.exe                # đã build sẵn, commit vào repo
├── Dockerfile, docker-compose.yml, .dockerignore
├── requirements.txt
├── footer.html             # nhúng cuối mọi trang, sửa trực tiếp được
├── .streamlit/config.toml  # toolbarMode = "minimal" (ẩn nút Deploy)
├── assets/logo-ueh.png, logo-ueh.ico
├── utils/                  # state, i18n, stats, export, project, report, footer
├── pages/1..7_*.py         # 6 module phân tích + User Guide
└── docs/claude_handover.md # chính là file này
```

## Lệnh hữu ích

```bash
# Chạy dev (đã có .venv)
.venv/Scripts/streamlit.exe run app.py

# Build lại DASS.exe sau khi sửa launcher.py
.venv/Scripts/python.exe -m PyInstaller --onefile --console --name DASS --icon assets/logo-ueh.ico launcher.py
cp dist/DASS.exe .
rm -rf build dist DASS.spec

# Docker (chưa test thật)
docker compose up --build
```
