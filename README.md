# Báo cáo Bộ phận Xếp Giấy – bản công khai trên Netlify

Ai có link đều xem được báo cáo và lọc theo Tháng / Tuần / Ngày / Line.
Bạn cập nhật số liệu bằng cách tải file Excel lên trang `upload.html` (cần mật khẩu).

Các file trong thư mục:
- `index.html`: báo cáo (giao diện giữ nguyên như Dashboard.html của bạn, số liệu nạp từ Supabase)
- `upload.html`: trang tải file Excel lên (đọc 3 sheet Nhap_TG, Nhap_SP, Nhap_BTP ngay trên trình duyệt)
- `parse-xlsx.js`: đoạn mã đọc Excel (cùng logic với update_dashboard.py)
- `config.js`: 2 giá trị kết nối Supabase
- `schema.sql`: tạo cơ sở dữ liệu

## Cài đặt một lần

### Bước 1. Tạo nơi lưu số liệu (Supabase, miễn phí)
1. Vào https://supabase.com, tạo tài khoản và một Project mới.
2. Mở `schema.sql`, đổi `DOI_MAT_KHAU_O_DAY` thành mật khẩu của bạn (dùng cho trang upload).
3. Trong Supabase: SQL Editor > New query > dán toàn bộ `schema.sql` > Run. Phải thấy "Success".
4. Project Settings > API: copy **Project URL** và khóa **anon public** (chuỗi dài bắt đầu bằng `eyJ`).

### Bước 2. Điền cấu hình
Mở `config.js`, dán Project URL và anon key vào hai dòng tương ứng. Lưu file.

### Bước 3. Đưa lên Netlify
Vào https://app.netlify.com/drop, kéo thả cả thư mục này lên. Netlify cấp link công khai, ví dụ
`https://ten-bao-cao.netlify.app`. Có thể đổi tên link trong Site settings.

### Bước 4. Đẩy số liệu lần đầu
Mở `link-của-bạn/upload.html`, làm theo 3 bước trên trang (chọn file, xem kiểm tra, nhập mật khẩu, bấm Đẩy lên).

## Dùng hằng ngày
1. Nhập dữ liệu vào file Excel như cũ (ba sheet Nhap_TG, Nhap_SP, Nhap_BTP), lưu file.
2. Mở `upload.html` (hoặc bấm "Cập nhật dữ liệu" ở cuối báo cáo), chọn file, kiểm tra số dòng và khoảng ngày.
3. Nhập mật khẩu, bấm **Đẩy lên báo cáo**.
4. Mọi người mở link là thấy số liệu mới. Trang đang mở tự tải lại sau khoảng 1 phút.

Đẩy nhầm file: bấm **Khôi phục bản trước** trên trang upload để quay về bản ngay trước đó.

Bạn vẫn dùng được `update_dashboard.py` như cũ: tải `dashboard_data.json` mà script tạo ra lên trang upload, kết quả giống nhau.

## Lưu ý
- Số liệu sản xuất hiển thị công khai với bất kỳ ai có link. Không gửi link ra ngoài nếu số liệu nội bộ.
  Cần giới hạn người xem thì bật mật khẩu cho site trong Netlify (Site configuration > Access control, gói trả phí)
  hoặc báo tôi để thêm màn hình đăng nhập.
- Khóa anon public được phép nằm trong file công khai. Người ngoài chỉ đọc được báo cáo; ghi dữ liệu cần mật khẩu,
  được kiểm tra ở máy chủ.
- Đổi mật khẩu: SQL Editor chạy
  `update settings set value = extensions.crypt('MAT_KHAU_MOI', extensions.gen_salt('bf')) where key = 'admin';`
- Chỉ tính các cột như file mẫu (Nhap_TG: A, C, D, E, N, O, R, T; Nhap_SP: A, B, D, E, G, K, L, N; Nhap_BTP: A, B, D, E, F, G, J, M).
  Không chèn thêm hoặc xóa cột trong ba sheet này; thêm dòng ở cuối thì được.
- Supabase gói miễn phí tạm dừng project sau khoảng 1 tuần không có truy cập. Vào dashboard bấm Restore để mở lại.

https://kuxrkqirrwdvklbmtwbx.supabase.co
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt1eHJrcWlycndkdmtsYm10d2J4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTM2NzI3MzMsImV4cCI6MjEwOTI0ODczM30.ot-JVRPtOAVCVVIz2byPdON2TiJfgI3H5s6OjgDUObQ
