import streamlit as st

from utils.i18n import t, get_lang
from utils.footer import render_footer

st.title(f"❓ {t('nav.help')}")

GUIDE_VI = r"""
### DASS là gì?

**DASS (UEH Data Analysis for Social Sciences)** là công cụ phân tích thống kê chạy trên web, tương tự SPSS, dành cho sinh viên/nhà nghiên cứu khoa học xã hội — làm sạch dữ liệu khảo sát, đánh giá thang đo, kiểm định giả thuyết và xuất báo cáo mà không cần cài phần mềm.

---

### 1. Bắt đầu

- **Ngôn ngữ**: dropdown 🌐 đầu sidebar — đổi Tiếng Việt/English áp dụng ngay cho toàn bộ ứng dụng.
- **Nhập dữ liệu**: mục "Import Data" ở sidebar — hỗ trợ CSV, Excel (.xlsx/.xls), SPSS (.sav). Hoặc bấm **"Use sample data (demo)"** để có ngay 200 quan sát mẫu (khảo sát về Tính xác thực thương hiệu & Ý định mua) để thử nghiệm mọi chức năng.
- Dữ liệu tồn tại trong suốt phiên làm việc (session) của trình duyệt. Đóng tab sẽ mất dữ liệu trừ khi bạn **Lưu dự án** (xem mục 7).

### 2. Trang chủ — Data View & Variable View

- **Data View**: bảng dữ liệu có thể **sửa trực tiếp** (thêm/xóa dòng, sửa ô) — thay đổi được **tự động lưu** ngay, không cần bấm nút riêng, và áp dụng ngay cho mọi phân tích/xuất file sau đó.
- **Variable View**: xem tổng quan từng biến (kiểu dữ liệu, N hợp lệ/khuyết, số giá trị duy nhất).
  - **Gán nhãn biến**: đặt mô tả dễ hiểu cho biến (ví dụ: `BA1` → "Thương hiệu này trung thực với chính mình").
  - **Chuyển đổi kiểu dữ liệu**: đổi một biến sang Số / Chữ / Ngày tháng / Phân loại — tương tự cột "Type" trong SPSS. Giá trị không chuyển đổi được sẽ báo rõ số lượng bị biến thành khuyết.

### 3. Quản lý & Biến đổi Dữ liệu (Data Management)

- **Recode**:
  - *Đảo điểm (Reverse Scoring)*: dùng cho phát biểu có ngữ nghĩa ngược trong thang Likert (ví dụ câu hỏi bị "lật ngược"). Chọn biến, nhập Min/Max thang đo, chọn ghi đè hoặc tạo biến mới (`_R`).
  - *Mã hóa tùy chỉnh*: đổi giá trị text/số sang giá trị khác, hoặc gộp nhóm (ví dụ gộp "18-24" và "25-34" thành "Trẻ").
- **Xử lý dữ liệu khuyết**: phát hiện ô trống, chọn cách xử lý — điền Mean/Median/Mode, hoặc loại bỏ quan sát (Listwise Deletion).
- **Tính biến mới (Compute)**: gộp nhiều item quan sát thành 1 biến đại diện (construct) bằng Trung bình cộng hoặc Tổng — ví dụ gộp `BA1..BA4` thành `BA_TB`.

### 4. Thống kê Mô tả (Descriptive Statistics)

- **Frequencies**: đếm tần số + tỷ lệ % (kể cả % hợp lệ, % tích lũy) — dùng cho biến định tính/nhân khẩu học.
- **Descriptives**: Mean, Std. Dev., Min/Max, Skewness, Kurtosis cho biến định lượng.
- **Crosstabs**: bảng chéo giữa 2 biến định tính, kèm kiểm định Chi-square và độ mạnh liên hệ (Cramér's V, Phi cho bảng 2×2).
- **Chi-square GOF**: so sánh phân bổ quan sát của 1 biến với phân bổ kỳ vọng (đều nhau hoặc tự nhập tỷ lệ).

### 5. Đánh giá Thang đo (Scale Evaluation)

- **Cronbach's Alpha**: đo độ tin cậy nội tại của một nhóm item. Alpha ≥ 0.7 thường được xem là chấp nhận được. Biến có tương quan biến-tổng < 0.3 nên cân nhắc loại bỏ.
- **EFA (Phân tích nhân tố khám phá)**: kiểm tra KMO/Bartlett trước, xem Scree Plot để chọn số nhân tố, rồi xem ma trận nhân tố (hệ số tải ≥ 0.5 được tô đậm) và phương sai trích.

### 6. Kiểm định Giả thuyết (Hypothesis Testing)

- **Independent T-Test**: so sánh trung bình giữa 2 nhóm độc lập (ví dụ Nam vs Nữ). Có Levene's Test (đồng nhất phương sai), Cohen's d và khoảng tin cậy 95% cho chênh lệch trung bình.
- **Paired T-Test**: so sánh 2 biến đo trên cùng đối tượng (trước/sau). Có Cohen's dz.
- **One-Way ANOVA**: so sánh trung bình giữa ≥3 nhóm, kèm eta²/omega² (độ lớn ảnh hưởng) và hậu định Tukey HSD khi có ý nghĩa.
- **Two-Way ANOVA**: kiểm tra tác động của 2 biến nhân tố và tương tác giữa chúng lên 1 biến phụ thuộc.

### 7. Phân tích Mối quan hệ (Relational Analysis)

- **Tương quan Pearson**: ma trận hệ số tương quan r + mức ý nghĩa, kèm heatmap.
- **Hồi quy tuyến tính/đa biến**: hệ số B, Beta chuẩn hóa, VIF (kiểm tra đa cộng tuyến), R²/Adjusted R², biểu đồ phần dư.

### 8. Phi tham số & Đồ thị (Non-parametric & Graphs)

- **Kiểm tra phân phối chuẩn (Shapiro-Wilk)**: giúp quyết định dùng kiểm định tham số hay phi tham số.
- **Mann-Whitney U** (thay Independent T-Test), **Kruskal-Wallis** (thay ANOVA), **Wilcoxon Signed-Rank** (thay Paired T-Test) — dùng khi dữ liệu lệch chuẩn hoặc mẫu nhỏ.
- **Graphs**: Histogram, Scatter Plot (có trendline), Box Plot, Bar Chart.

### 9. Báo cáo kết quả & Xuất file

- Ở **mỗi** phân tích, tick ô **"➕ Add results to the report when run"** trước khi bấm nút chạy — kết quả sẽ được gom vào báo cáo.
- Mục **"Analysis Report"** ở sidebar cho tải về file **Word (.docx)** tổng hợp mọi kết quả đã gom (kèm bảng số liệu), có thể chỉnh sửa tiếp trong Word. Có nút xóa báo cáo để làm lại từ đầu.
- Mục **"Export Data"** ở sidebar tải về **CSV/Excel** của bộ dữ liệu hiện tại (đã áp dụng mọi Recode/Compute/xử lý khuyết/sửa tay).

### 10. Lưu & Mở lại dự án (Project)

- **Save project**: xuất 1 file `.json` chứa toàn bộ: dữ liệu, nhãn biến, nhật ký xử lý, và báo cáo đang gom.
- **Open project**: tải file `.json` đó lên để khôi phục đúng như lúc lưu — tiếp tục làm việc mà không mất gì.

### Mẹo nhỏ

- Xử lý dữ liệu khuyết **trước** khi chạy EFA/Cronbach's Alpha để tránh mất quá nhiều quan sát.
- Nếu Shapiro-Wilk báo dữ liệu không chuẩn (p < 0.05) và cỡ mẫu nhỏ, cân nhắc dùng kiểm định phi tham số tương ứng thay vì T-Test/ANOVA.
- Nhật ký xử lý (expander "Processing log" cuối trang Biến đổi Dữ liệu) ghi lại mọi thao tác đã làm trong phiên — hữu ích để kiểm tra lại quy trình.
"""

GUIDE_EN = r"""
### What is DASS?

**DASS (UEH Data Analysis for Social Sciences)** is a browser-based statistics tool, similar to SPSS, built for social-science students and researchers — clean survey data, evaluate measurement scales, test hypotheses, and export a report, with no software installation required.

---

### 1. Getting Started

- **Language**: the 🌐 dropdown at the top of the sidebar — switching applies instantly across the whole app.
- **Import data**: the "Import Data" section in the sidebar — supports CSV, Excel (.xlsx/.xls), and SPSS (.sav). Or click **"Use sample data (demo)"** for 200 ready-made observations (a Brand Authenticity & Purchase Intention survey) to try every feature immediately.
- Data lives for the duration of your browser session. Closing the tab loses it unless you **save the project** (see section 7).

### 2. Home — Data View & Variable View

- **Data View**: an editable data grid (add/delete rows, edit cells) — changes are **saved automatically**, no separate save step, and apply instantly to every later analysis and export.
- **Variable View**: an overview of every variable (data type, N valid/missing, unique values).
  - **Assign a label**: give a variable a readable description (e.g. `BA1` → "This brand is true to itself").
  - **Change data type**: convert a variable to Numeric / Text / Date / Category — similar to the "Type" column in SPSS. Values that fail to convert are reported so you know how many became missing.

### 3. Data Management & Transformation

- **Recode**:
  - *Reverse Scoring*: for reverse-worded statements in a Likert scale. Pick the variable(s), enter the scale's Min/Max, choose to overwrite or create a new `_R` variable.
  - *Custom Recode*: map values to new ones, or merge groups (e.g. combine "18-24" and "25-34" into "Young").
- **Missing Data**: detects blank cells; choose to fill with Mean/Median/Mode, or remove affected observations (Listwise Deletion).
- **Compute Variable**: combine several observed items into one overall construct variable, via Mean or Sum — e.g. combine `BA1..BA4` into `BA_avg`.

### 4. Descriptive Statistics

- **Frequencies**: counts and percentages (including valid % and cumulative %) — for categorical/demographic variables.
- **Descriptives**: Mean, Std. Dev., Min/Max, Skewness, Kurtosis for quantitative variables.
- **Crosstabs**: a cross-tabulation of two categorical variables, with a Chi-square test and strength of association (Cramér's V, Phi for 2×2 tables).
- **Chi-square GOF**: compares one variable's observed distribution against an expected one (equal proportions, or your own custom proportions).

### 5. Scale Evaluation

- **Cronbach's Alpha**: measures the internal-consistency reliability of a group of items. Alpha ≥ 0.7 is usually considered acceptable. Items with a corrected item-total correlation < 0.3 are candidates for removal.
- **EFA (Exploratory Factor Analysis)**: check KMO/Bartlett first, use the Scree Plot to pick the number of factors, then review the component matrix (loadings ≥ 0.5 are bolded) and variance explained.

### 6. Hypothesis Testing

- **Independent T-Test**: compares the mean between 2 independent groups (e.g. Male vs. Female). Includes Levene's Test (equality of variances), Cohen's d, and a 95% CI for the mean difference.
- **Paired T-Test**: compares two variables measured on the same subjects (before/after). Includes Cohen's dz.
- **One-Way ANOVA**: compares the mean across ≥3 groups, with eta²/omega² (effect size) and Tukey HSD post-hoc when significant.
- **Two-Way ANOVA**: tests the effect of two factor variables — and their interaction — on one dependent variable.

### 7. Relational Analysis

- **Pearson Correlation**: a correlation coefficient matrix with significance levels, plus a heatmap.
- **Linear/Multiple Regression**: B coefficients, standardized Beta, VIF (multicollinearity check), R²/Adjusted R², and a residuals plot.

### 8. Non-parametric & Graphs

- **Normality check (Shapiro-Wilk)**: helps decide between a parametric or non-parametric test.
- **Mann-Whitney U** (replaces Independent T-Test), **Kruskal-Wallis** (replaces ANOVA), **Wilcoxon Signed-Rank** (replaces Paired T-Test) — use when data is skewed or the sample is small.
- **Graphs**: Histogram, Scatter Plot (with trendline), Box Plot, Bar Chart.

### 9. Building a Report & Exporting Files

- On **every** analysis, tick **"➕ Add results to the report when run"** before clicking Run — the results get collected into the report.
- The **"Analysis Report"** section in the sidebar lets you download a combined **Word (.docx)** file with every collected result (including data tables), ready to keep editing in Word. A "Clear report" button lets you start over.
- The **"Export Data"** section in the sidebar downloads the current dataset as **CSV/Excel** (with every Recode/Compute/missing-data fix/manual edit already applied).

### 10. Saving & Reopening a Project

- **Save project**: exports a single `.json` file containing everything — data, variable labels, the processing log, and the report you've collected so far.
- **Open project**: upload that `.json` file to restore exactly where you left off — no data lost.

### Tips

- Handle missing data **before** running EFA/Cronbach's Alpha to avoid losing too many observations.
- If Shapiro-Wilk reports non-normal data (p < 0.05) and the sample is small, consider the matching non-parametric test instead of a T-Test/ANOVA.
- The processing log (the "Processing log" expander at the bottom of the Data Management page) records every action taken this session — useful for double-checking your workflow.
"""

st.markdown(GUIDE_VI if get_lang() == "vi" else GUIDE_EN)

render_footer()
