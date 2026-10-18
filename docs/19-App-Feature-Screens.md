# Danang TourGuide — Chức năng và màn hình ứng dụng

> Bản phác thảo chức năng cho ứng dụng mobile, ưu tiên MVP/P0. Mục tiêu là giúp khách du lịch khám phá địa điểm Đà Nẵng, tạo lịch trình và được hỗ trợ khi đang tham quan.

## 1. Mục tiêu và luồng chính

**Người dùng chính:** khách du lịch Việt Nam, chưa quen Đà Nẵng, muốn tìm điểm đến đáng tin cậy và có lịch trình dễ theo dõi.

```text
Khám phá → Xem địa điểm → Lưu / tạo chuyến đi → Nhập sở thích
→ AI đề xuất lịch trình → Chỉnh sửa → Bắt đầu chuyến đi
→ Đến điểm tham quan → Nghe thuyết minh / hỏi AI → Hoàn thành chuyến đi
```

Thanh điều hướng chính gồm 4 tab: **Khám phá · Chuyến đi · Đã lưu · Cài đặt**. Bản đồ, trình phát audio và Hỏi AI là màn hình/phần mở theo ngữ cảnh.

## 2. Nhóm tính năng

| Nhóm | Tính năng MVP (P0) | Giá trị cho người dùng |
|---|---|---|
| Khám phá địa điểm | Danh mục, tìm kiếm, lọc, xem bản đồ, xem chi tiết | Tìm nhanh nơi phù hợp để đi |
| Thông tin đáng tin cậy | Mô tả, ảnh được kiểm duyệt, tọa độ, nguồn tham khảo, ngày cập nhật | Biết thông tin nào có căn cứ; không đoán giờ mở cửa/giá vé khi thiếu dữ liệu |
| Lưu địa điểm | Lưu/bỏ lưu, xem danh sách đã lưu, thêm vào lịch trình | Gom các điểm muốn đi |
| Lập lịch trình AI | Nhập sở thích/ràng buộc, AI đề xuất các điểm, cảnh báo xung đột | Có kế hoạch khởi đầu thay vì tự sắp từng điểm |
| Chỉnh sửa lịch trình | Thêm, xoá, đổi thứ tự, đổi thời lượng, xem tuyến đường | Người dùng luôn là người quyết định lịch trình |
| Bản đồ & di chuyển | Marker theo thứ tự, đường đi, phương tiện và thời điểm lấy ước tính | Dễ hình dung vị trí và thứ tự ghé thăm |
| Chế độ tham quan | Bắt đầu chuyến, điểm hiện tại/tiếp theo, hoàn thành/bỏ qua điểm | Theo dõi chuyến đi ngoài thực tế |
| GPS đến địa điểm | Nhận diện đến điểm hiện tại khi app đang mở; chọn xác nhận thủ công khi GPS yếu/từ chối quyền | Hỗ trợ đúng lúc, không tuyên bố sai rằng GPS đã xác nhận |
| Audio guide | Audio do người thu âm, phát/tạm dừng/tua, transcript | Nghe thuyết minh tại các điểm có nội dung |
| Hỏi AI theo ngữ cảnh | Hỏi về điểm/chuyến đang xem; câu trả lời có nguồn hoặc báo thiếu bằng chứng | Hiểu sâu hơn mà vẫn phân biệt thông tin có/không có căn cứ |
| Tài khoản | Đăng ký, đăng nhập, đăng xuất; đồng bộ chuyến đi và địa điểm đã lưu | Bảo vệ dữ liệu cá nhân và dùng trên nhiều thiết bị |

### Ngoài phạm vi MVP

- Nhận diện địa danh qua camera, nhập câu hỏi bằng giọng nói và Google Sign-In: **P1**, chỉ làm sau khi P0 hoàn chỉnh.
- Không bao gồm đặt vé/thanh toán, mạng xã hội, chatbot nói chuyện bằng giọng nói, TTS, theo dõi GPS nền, thông báo tự động hay offline hoàn chỉnh.

## 3. Bản đồ màn hình đầy đủ

Mỗi **screen** là một trang điều hướng. Các **sheet/modal** là màn hình nhỏ mở đè lên trang hiện tại; cần thiết kế và xử lý trạng thái riêng, không xem là “chỉ một popup”.

```text
Khởi động / Onboarding
  └─ Xác thực (Đăng nhập, Đăng ký, OTP, Quên/Đặt lại mật khẩu)
       └─ Tabs: Khám phá · Chuyến đi · Đã lưu · Cài đặt
            ├─ Địa điểm / Bản đồ / Nguồn / Audio / Hỏi AI
            ├─ Tạo, xem trước, chỉnh sửa, bản đồ và tham quan chuyến đi
            └─ Các sheet xác nhận, quyền thiết bị và trạng thái lỗi
```

### 3.1. Khởi động và onboarding

| ID | Screen | Trong màn hình có gì | Hành động / điều hướng |
|---|---|---|---|
| APP-01 | Splash | Logo Danang TourGuide, trạng thái kiểm tra phiên đăng nhập và kết nối tối thiểu | Có phiên hợp lệ → Tab Khám phá; chưa có → Onboarding/Đăng nhập. Không hiển thị lỗi kỹ thuật dài dòng. |
| APP-02 | Onboarding 1 — Khám phá | Ảnh minh hoạ Đà Nẵng, tiêu đề “Khám phá địa điểm”, mô tả ngắn, chấm tiến trình | Tiếp tục, Bỏ qua. |
| APP-03 | Onboarding 2 — Lập lịch trình | Minh hoạ timeline/bản đồ, mô tả AI hỗ trợ lên kế hoạch | Quay lại, Tiếp tục, Bỏ qua. |
| APP-04 | Onboarding 3 — Tham quan | Minh hoạ GPS/audio, giải thích quyền vị trí chỉ dùng khi bắt đầu chuyến đi | Bắt đầu khám phá (không bắt buộc đăng nhập). |
| APP-05 | Chọn ngôn ngữ | Tiếng Việt mặc định; English chỉ hiển thị khi nội dung hỗ trợ; nút lưu | Lưu lựa chọn → Khám phá. Có thể đổi lại trong Cài đặt. |

### 3.2. Tài khoản và xác thực

| ID | Screen | Trong màn hình có gì | Hành động / kiểm tra |
|---|---|---|---|
| AUTH-01 | Chọn cách bắt đầu | Logo, lợi ích đăng nhập, nút Đăng nhập, Tạo tài khoản, “Khám phá với tư cách khách” | Khách chỉ được xem dữ liệu công khai; các hành động riêng tư chuyển sang Đăng nhập. |
| AUTH-02 | Đăng nhập | Email, mật khẩu, nút hiện/ẩn mật khẩu, “Quên mật khẩu?”, nút Đăng nhập, liên kết Đăng ký | Kiểm tra email/mật khẩu; lỗi sai thông tin, lỗi mạng, tài khoản chưa xác minh. Google Sign-In là P1. |
| AUTH-03 | Đăng ký | Họ tên hiển thị (tuỳ chọn), email, mật khẩu, xác nhận mật khẩu, điều khoản/quyền riêng tư, nút Tạo tài khoản | Kiểm tra định dạng email, mật khẩu mạnh và mật khẩu khớp; thành công chuyển sang OTP. |
| AUTH-04 | Xác thực OTP email | Email được che một phần, 6 ô OTP, đếm ngược gửi lại, đổi email, nút Xác thực | Tự chuyển ô, dán mã, báo mã sai/hết hạn; gửi lại OTP có giới hạn chống spam. |
| AUTH-05 | OTP thành công | Biểu tượng thành công, thông báo tài khoản đã xác thực | Đi tới Khám phá hoặc quay lại tác vụ đang bị chặn. |
| AUTH-06 | Quên mật khẩu | Ô email, mô tả cách nhận mã, nút Gửi mã | Không tiết lộ email có tồn tại hay không; sang OTP đặt lại mật khẩu. |
| AUTH-07 | OTP đặt lại mật khẩu | Email che một phần, 6 ô OTP, gửi lại mã/đổi email | Mã hợp lệ → Đặt lại mật khẩu. |
| AUTH-08 | Đặt lại mật khẩu | Mật khẩu mới, xác nhận, hiện/ẩn mật khẩu, yêu cầu mật khẩu, nút Lưu | Lưu thành công → thông báo → Đăng nhập bằng mật khẩu mới. |
| AUTH-09 | Phiên hết hạn | Giải thích phiên đăng nhập đã hết hạn, nút Đăng nhập lại | Giữ nguyên dữ liệu công khai và màn hình trước đó; sau login quay lại tác vụ nếu an toàn. |

### 3.3. Khám phá địa điểm

| ID | Screen | Trong màn hình có gì | Hành động / trạng thái |
|---|---|---|---|
| EXP-01 | Khám phá (tab) | Header chào mừng, ô tìm kiếm, chip danh mục, khu vực “Gợi ý”, thẻ địa điểm (ảnh, tên, tag, khu vực), bottom tab | Mở tìm kiếm, lọc, chi tiết hoặc bản đồ. Có skeleton khi tải. |
| EXP-02 | Kết quả tìm kiếm | Ô tìm kiếm có nút xoá, lịch sử gần đây (cục bộ), số kết quả, thẻ POI | Tìm theo tên/tag tiếng Việt; không có kết quả hiển thị gợi ý xoá bộ lọc. |
| EXP-03 | Bộ lọc địa điểm (bottom sheet) | Danh mục, tag/sở thích, nút Xoá tất cả và Áp dụng, số lượng kết quả | Áp dụng bộ lọc; bộ lọc đang chọn hiển thị lại ở Khám phá. |
| EXP-04 | Bản đồ khám phá | Bản đồ, marker POI, nút vị trí hiện tại, nút quay lại danh sách, attribution nhà cung cấp | Chọn marker → sheet địa điểm; vị trí bị từ chối vẫn xem được bản đồ. |
| EXP-05 | Sheet địa điểm trên bản đồ | Ảnh thumbnail, tên, tag, khoảng cách chỉ khi có quyền vị trí, nút Xem chi tiết | Mở EXP-06. |
| EXP-06 | Chi tiết địa điểm | Gallery, tên, danh mục/tag, mô tả, tọa độ/địa chỉ, giờ/giá nếu có, thời lượng gợi ý, nguồn và ngày cập nhật, audio, nút Lưu/Thêm vào chuyến đi/Hỏi AI | Vuốt ảnh, mở nguồn, lưu, thêm vào hành trình, phát audio, hỏi AI. Dữ liệu thiếu phải ghi rõ “Chưa có thông tin”. |
| EXP-07 | Gallery ảnh toàn màn hình | Ảnh lớn, chỉ số ảnh, mô tả/credit, nút đóng | Vuốt ảnh; xem nguồn/credit ảnh khi có. |
| EXP-08 | Nguồn thông tin địa điểm | Danh sách nguồn: tiêu đề, đơn vị, ngày, đoạn thông tin liên quan, liên kết ngoài nếu có | Mở liên kết bằng trình duyệt; quay lại chi tiết. |
| EXP-09 | Chọn chuyến đi để thêm điểm (sheet) | Danh sách chuyến đi `draft/planned`, tìm chuyến đi, nút Tạo chuyến mới | Chọn một chuyến → xác nhận thêm; không thêm trùng. |
| EXP-10 | Xác nhận thêm điểm | Tên địa điểm, chuyến đi/ngày sẽ thêm, cảnh báo tuyến đường cần cập nhật | Xác nhận/huỷ; thành công có snackbar và nút xem lịch trình. |

### 3.4. Lưu địa điểm và quản lý chuyến đi

| ID | Screen | Trong màn hình có gì | Hành động / trạng thái |
|---|---|---|---|
| SAV-01 | Đã lưu (tab) | Tiêu đề, tìm kiếm trong danh sách đã lưu, thẻ địa điểm, nút bỏ lưu/thêm vào chuyến đi | Mở chi tiết, bỏ lưu, thêm vào chuyến đi. Trạng thái rỗng có nút Khám phá. |
| SAV-02 | Xác nhận bỏ lưu (sheet) | Tên địa điểm, giải thích hành động | Bỏ lưu/giữ lại. Có thể dùng undo snackbar sau khi thành công. |
| TRIP-01 | Chuyến đi (tab) | Nút Tạo chuyến đi, nhóm Nháp/Sắp diễn ra/Đang tham quan/Đã hoàn thành, thẻ chuyến đi | Mở chi tiết, tiếp tục chuyến đang active, tạo chuyến. Trạng thái rỗng có CTA. |
| TRIP-02 | Tạo chuyến đi — thông tin cơ bản | Tên chuyến (tuỳ chọn), ngày bắt đầu, số ngày, điểm xuất phát | Tiếp tục; kiểm tra ngày và giới hạn số ngày. |
| TRIP-03 | Tạo chuyến đi — sở thích | Danh mục sở thích chọn nhiều, nhịp độ chậm/vừa/nhanh, ngân sách định tính | Tiếp tục/quay lại. |
| TRIP-04 | Tạo chuyến đi — di chuyển & thời gian | Phương tiện, giờ bắt đầu/kết thúc mỗi ngày, tóm tắt lựa chọn | Tạo nháp và “Tạo lịch trình AI”. |
| TRIP-05 | Đang tạo lịch trình AI | Animation tải không dùng phần trăm giả, tóm tắt yêu cầu, nút Huỷ chờ | Hoàn tất → xem trước; lỗi/time-out → trạng thái lỗi nhưng giữ nháp. |
| TRIP-06 | Xem trước lịch trình AI | Tab ngày, timeline điểm dừng, thời lượng gợi ý, tuyến đường, panel cảnh báo/thiếu dữ liệu, nút Chấp nhận/Tạo lại/Sửa yêu cầu | Chấp nhận sau khi xem; lỗi ràng buộc chắc chắn chặn chấp nhận. |
| TRIP-07 | Chi tiết lịch trình | Tiêu đề/trạng thái chuyến, chọn ngày, các điểm theo thứ tự, route status, cảnh báo, nút Sửa/Bản đồ/Bắt đầu chuyến | Mở sửa, bản đồ, bắt đầu; nháp chưa có kế hoạch chỉ hiển thị tạo đề xuất. |
| TRIP-08 | Sửa lịch trình | Danh sách điểm có số thứ tự, kéo-thả và nút Lên/Xuống hỗ trợ accessibility, sửa thời lượng, xoá điểm, thêm điểm | Lưu thay đổi nguyên tử; hiện cảnh báo route stale sau sửa. Không cho sửa điểm hiện tại/đã đi khi active. |
| TRIP-09 | Thêm điểm vào ngày (sheet) | Tìm kiếm/lọc POI, danh sách kết quả, ngày đang thêm | Chọn điểm → thêm vào cuối hoặc chọn vị trí; ngăn trùng điểm. |
| TRIP-10 | Sửa thời lượng điểm (sheet) | Tên điểm, stepper/ô số phút, thời lượng gợi ý, xác nhận | Lưu; kiểm tra giới hạn thời lượng. |
| TRIP-11 | Xác nhận xoá điểm (sheet) | Tên điểm, ảnh hưởng đến tuyến đường/lịch | Xoá/huỷ; nếu ngày trống phải hiển thị cảnh báo chặn Start. |
| TRIP-12 | Bản đồ chuyến đi | Marker đánh số, polyline từng chặng, danh sách chặng, phương tiện, thời gian và thời điểm cập nhật | Chọn marker/chặng; thời lượng không có dữ liệu hiển thị “Chưa có ước tính”. |
| TRIP-13 | Chi tiết chặng đường (sheet) | Điểm đi/đến, khoảng cách/thời lượng nếu có, phương tiện, thời điểm lấy dữ liệu, trạng thái fresh/stale/unavailable | Đóng/quay lại; không gọi đây là ETA được đảm bảo. |
| TRIP-14 | Xác nhận bắt đầu chuyến đi | Tóm tắt ngày đầu, cảnh báo còn lại, checkbox đã hiểu bất định, giải thích GPS foreground và toggle tự phát audio mặc định tắt | Bắt đầu khi không có lỗi chặn; chuyển Travel mode. |
| TRIP-15 | Chuyến đi hoàn thành | Tóm tắt số điểm hoàn thành/bỏ qua, ngày kết thúc, nút xem lại lịch trình/khám phá tiếp | Không chỉnh sửa lịch sử điểm; quay về tab Chuyến đi. |

### 3.5. Chế độ tham quan, GPS và audio

| ID | Screen | Trong màn hình có gì | Hành động / trạng thái |
|---|---|---|---|
| LIVE-01 | Chế độ tham quan | Bản đồ vùng hiện tại, tên/ảnh điểm hiện tại, điểm kế tiếp, tiến độ, GPS status, nút Hướng dẫn đường, Đã đến, Hoàn thành/Bỏ qua, Ask | Chỉ theo dõi GPS khi app mở và screen này hoạt động. |
| LIVE-02 | Giải thích quyền vị trí (sheet) | Lý do dùng vị trí, “chỉ khi tham quan”, phương án xác nhận thủ công | Cho phép/Không phải bây giờ. Không ép quyền để tiếp tục. |
| LIVE-03 | Vị trí bị từ chối/yếu (sheet) | Trạng thái quyền hoặc độ chính xác, hướng dẫn bật lại, nút Xác nhận đã đến thủ công | Mở cài đặt hệ thống hoặc xác nhận thủ công. |
| LIVE-04 | Xác nhận đến thủ công | Tên điểm hiện tại, nhãn “Thủ công”, lý do chọn (tuỳ chọn), xác nhận | Tạo arrival event dạng manual; không ghi là GPS. |
| LIVE-05 | Đã đến địa điểm (arrival sheet) | Tên/ảnh điểm, phương thức GPS/thủ công/mô phỏng, audio có sẵn, nút Hỏi AI, thông tin điểm tiếp theo | Mở audio/Ask, đóng để tiếp tục tham quan. |
| LIVE-06 | Xác nhận hoàn thành/bỏ qua điểm | Tên điểm, lựa chọn Hoàn thành hoặc Bỏ qua, lý do bỏ qua tuỳ chọn | Chuyển điểm tiếp theo; điểm cuối → TRIP-15. |
| LIVE-07 | Audio guide | Ảnh/tên POI, người thuyết minh, ngôn ngữ, play/pause, tua ±15 giây, tiến độ, tốc độ phát, transcript | Điều khiển audio; asset thiếu → Audio unavailable. |
| LIVE-08 | Transcript audio | Văn bản transcript, phần đang phát được highlight nếu hỗ trợ, cỡ chữ | Đóng/quay về player; không cần micro. |
| LIVE-09 | Audio không khả dụng (sheet) | Lý do: chưa có audio/không có ngôn ngữ/không tải được, transcript nếu có | Đọc transcript, thử lại (lỗi mạng), đóng. |

### 3.6. Hỏi AI, cài đặt và màn hình dùng chung

| ID | Screen | Trong màn hình có gì | Hành động / trạng thái |
|---|---|---|---|
| AI-01 | Hỏi AI | Chip ngữ cảnh POI/chuyến đi, lịch sử câu hỏi, ô nhập đa dòng, nút Gửi, câu trả lời và thẻ nguồn | Gửi câu hỏi; không có mic ở P0. Câu trả lời thiếu bằng chứng phải có trạng thái riêng. |
| AI-02 | Chi tiết nguồn AI (sheet) | Claim/câu trả lời liên quan, nguồn, đoạn trích hỗ trợ, ngày/corpus version nếu có | Mở nguồn đầy đủ/đóng. |
| AI-03 | AI thiếu bằng chứng | Giải thích không đủ nguồn tin cậy, gợi ý câu hỏi khác hoặc mở nguồn POI | Sửa câu hỏi, quay lại chi tiết. |
| AI-04 | AI tạm không khả dụng | Lỗi provider/network rõ ràng, nút Thử lại và quay lại | Không tự tạo câu trả lời giả. |
| SET-01 | Cài đặt (tab) | Avatar/tên/email, ngôn ngữ, quyền vị trí, trợ giúp, quyền riêng tư, đăng xuất | Mở các trang thiết lập chi tiết. |
| SET-02 | Tài khoản | Thông tin cơ bản, trạng thái email đã xác minh, đổi mật khẩu | Mở AUTH-06/luồng đổi mật khẩu; không hiển thị mật khẩu hiện tại. |
| SET-03 | Quyền & vị trí | Trạng thái Location, giải thích cách app dùng quyền, nút Mở cài đặt hệ thống | Không tự bật quyền; có hướng dẫn fallback thủ công. |
| SET-04 | Ngôn ngữ | Danh sách ngôn ngữ, mô tả phạm vi nội dung/audio hiện có | Lưu và tải lại UI/nội dung phù hợp. |
| SET-05 | Giới thiệu & quyền riêng tư | Phiên bản app, chính sách quyền riêng tư, điều khoản, liên hệ phản hồi | Mở liên kết ngoài khi có. |
| SET-06 | Xác nhận đăng xuất | Email hiện tại, thông báo dữ liệu cục bộ cần đồng bộ, nút Đăng xuất | Đăng xuất và thu hồi phiên → AUTH-01. |
| COM-01 | Lỗi mạng toàn cục | Minh hoạ offline, mô tả ngắn, Thử lại, quay lại dữ liệu đã tải | Không xoá form/nháp người dùng đang nhập. |
| COM-02 | Không có quyền truy cập | Icon khoá, giải thích yêu cầu đăng nhập/quyền sở hữu | Đăng nhập hoặc quay lại. |
| COM-03 | Màn hình tải | Skeleton đúng ngữ cảnh (thẻ, detail, timeline) | Không chặn điều hướng không cần thiết. |
| COM-04 | Snackbar/toast | Thông báo ngắn: đã lưu, đã bỏ lưu, đã thêm điểm, lỗi lưu; action Undo khi phù hợp | Tự ẩn, có screen-reader announcement. |
| COM-05 | Xác nhận rời form chưa lưu | Nội dung thay đổi chưa lưu, nút Rời đi/Ở lại | Chỉ hiện khi có dữ liệu người dùng chưa ghi nhận. |

### 3.7. Màn hình P1 (không chặn MVP)

| ID | Screen | Trong màn hình có gì | Hành động |
|---|---|---|---|
| P1-01 | Camera nhận diện địa danh | Permission, camera preview, chụp/chọn ảnh, khung hướng dẫn | Gửi ảnh để tìm ứng viên POI đã công bố; không tự tạo POI. |
| P1-02 | Kết quả nhận diện | Ảnh đã chụp, một hoặc nhiều ứng viên, trạng thái không nhận diện được | Người dùng xác nhận rồi mở chi tiết, hoặc tự tìm kiếm. |
| P1-03 | Nhập câu hỏi bằng giọng nói | Trạng thái ghi âm, waveform, văn bản nhận dạng có thể sửa, nút dùng văn bản | Cấp micro khi người dùng bấm; lỗi/từ chối → quay về gõ chữ. |

## 4. Quy tắc trải nghiệm quan trọng

- **Khách chưa đăng nhập** vẫn có thể Khám phá và xem chi tiết. Lưu địa điểm, tạo/lưu chuyến đi và Hỏi AI yêu cầu đăng nhập.
- Mỗi địa điểm hiển thị rõ nguồn tham khảo và dữ liệu thiếu. Ví dụ: “Chưa có thông tin giờ mở cửa” không được hiển thị là “Đang mở”.
- AI chỉ đề xuất từ danh sách địa điểm đã được công bố/kiểm duyệt; người dùng phải bấm **Chấp nhận** trước khi trở thành lịch trình chính thức.
- Cảnh báo biết chắc (ngày trống, địa điểm đóng cửa, vượt khung giờ) chặn nút Bắt đầu. Cảnh báo chưa chắc (thiếu giờ mở cửa, thiếu thời gian tuyến đường) phải được người dùng xác nhận.
- Khi chuyến đi đang hoạt động, chỉ các điểm **sắp tới** được sửa; điểm hiện tại hoặc đã hoàn thành/bỏ qua được giữ nguyên.
- GPS chỉ hoạt động khi người dùng đang mở app trong chế độ tham quan. Nếu GPS không chính xác hoặc không được cấp quyền, luôn có luồng **xác nhận thủ công**, kèm nhãn phân biệt với GPS.
- Audio là file thuyết minh được chuẩn bị sẵn. Nếu điểm chưa có audio hoặc không có đúng ngôn ngữ, hiển thị “Chưa có audio”, không tự tạo giọng đọc.
- Câu trả lời AI phải có nguồn hỗ trợ, hoặc trả lời minh bạch “Chưa đủ thông tin đáng tin cậy”/“Dịch vụ tạm không khả dụng”.

## 5. Dữ liệu tối thiểu cần có

### Địa điểm (POI)

- ID, tên tiếng Việt (và ngôn ngữ khác nếu có), danh mục/tag.
- Mô tả, ảnh đã có quyền sử dụng, tọa độ đã kiểm tra.
- Giờ mở cửa/giá vé nếu có nguồn; trạng thái `unknown` khi thiếu.
- Nguồn tham khảo và ngày cập nhật.
- Thời lượng tham quan gợi ý, audio guide và transcript nếu đã được duyệt.

### Chuyến đi

- Chủ sở hữu, tiêu đề, trạng thái: `draft → planned → active → completed`.
- Sở thích/ràng buộc đã nhập và danh sách điểm theo ngày/thứ tự.
- Thời lượng từng điểm, các chặng đường, cảnh báo và thời điểm cập nhật tuyến đường.
- Trạng thái từng điểm: `upcoming → current → completed/skipped`.

## 6. Ưu tiên triển khai đề xuất

1. **Khám phá + chi tiết địa điểm + dữ liệu POI**: tạo được ứng dụng có nội dung để demo.
2. **Đăng nhập + lưu địa điểm**: có dữ liệu cá nhân cơ bản.
3. **Tạo/xem trước/chỉnh sửa lịch trình**: hoàn thành luồng giá trị chính.
4. **Bản đồ tuyến đường + chế độ tham quan + GPS thủ công**: hoàn thiện trải nghiệm tại chỗ.
5. **Audio guide + Hỏi AI có nguồn**: tạo điểm khác biệt cho đồ án.
6. Chỉ sau khi các phần trên ổn định mới cân nhắc P1 camera/STT.

## 7. Tiêu chí demo MVP

Người dùng có thể hoàn thành toàn bộ kịch bản: tìm “Bảo tàng Chăm” → xem thông tin và nguồn → lưu → nhập sở thích để tạo lịch trình 1 ngày → chấp nhận, đổi thứ tự một điểm → xem bản đồ → bắt đầu chuyến đi → xác nhận đến (GPS hoặc thủ công) → nghe audio → hỏi một câu có nguồn → hoàn thành/bỏ qua điểm và kết thúc chuyến đi.
