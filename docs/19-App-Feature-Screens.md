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

## 3. Danh sách màn hình chi tiết

| ID | Màn hình | Mục đích | Thành phần chính | Hành động chính |
|---|---|---|---|---|
| UI-01 | Khám phá | Duyệt địa điểm | Ô tìm kiếm, chip danh mục, danh sách thẻ địa điểm, nút chuyển bản đồ | Tìm/lọc, mở chi tiết, mở bản đồ |
| UI-02 | Bản đồ khám phá | Xem các địa điểm trên bản đồ | Marker, điều khiển vị trí hiện tại, bottom sheet điểm được chọn | Chọn marker, mở chi tiết |
| UI-03 | Chi tiết địa điểm | Cung cấp thông tin trước khi ghé thăm | Gallery ảnh, tên/danh mục, mô tả, thông tin đã xác minh, nguồn/ngày cập nhật, trạng thái audio, nút Lưu/Thêm vào chuyến đi/Hỏi AI | Lưu, thêm vào lịch trình, nghe audio, hỏi AI |
| UI-04 | Tạo chuyến đi | Thu thập ràng buộc để tạo lịch trình | Ngày đi, số ngày, điểm xuất phát, sở thích, nhịp độ, khung giờ, ngân sách định tính, phương tiện | Kiểm tra dữ liệu, tạo đề xuất |
| UI-05 | Xem trước lịch trình AI | Cho người dùng xét và chấp nhận đề xuất | Timeline theo ngày, các điểm dừng, thời lượng gợi ý, cảnh báo/xung đột, trạng thái tạo | Chấp nhận, tạo lại, quay lại sửa yêu cầu |
| UI-06 | Chi tiết/chỉnh sửa lịch trình | Điều chỉnh kế hoạch đã chấp nhận | Chọn ngày, danh sách điểm đánh số, kéo-thả, thời lượng, trạng thái tuyến đường, thêm điểm, nút Bản đồ/Bắt đầu | Thêm/xoá/đổi thứ tự, đổi thời lượng, xem bản đồ, bắt đầu |
| UI-07 | Bản đồ chuyến đi | Xem thứ tự và các chặng di chuyển | Marker đánh số, polyline từng chặng, bottom sheet điểm dừng, nhãn phương tiện/thời gian/cập nhật | Chọn điểm dừng, quay lại chỉnh sửa |
| UI-08 | Chế độ tham quan | Điều hướng trạng thái trong chuyến đi | Điểm hiện tại/kế tiếp, bản đồ vùng lân cận, trạng thái GPS, nút xác nhận đến thủ công, Hoàn thành/Bỏ qua | Ghi nhận đến, hoàn thành/bỏ qua, mở audio/Hỏi AI |
| UI-09 | Sheet đã đến địa điểm | Phản hồi khi người dùng đến điểm hiện tại | Tên điểm, cách xác nhận (GPS/thủ công/mô phỏng), nút audio, Hỏi AI, xem điểm tiếp theo | Phát audio, hỏi AI, tiếp tục |
| UI-10 | Audio guide | Nghe thuyết minh | Tên người thuyết minh, ngôn ngữ, play/pause, thanh tiến độ, tua, transcript | Điều khiển phát, đọc transcript |
| UI-11 | Đã lưu | Quản lý địa điểm yêu thích | Danh sách địa điểm đã lưu, trạng thái rỗng, nút bỏ lưu/thêm vào chuyến đi | Mở chi tiết, bỏ lưu, thêm vào lịch trình |
| UI-12 | Đăng nhập/Đăng ký | Xác thực tài khoản | Email, mật khẩu, xác nhận mật khẩu, lỗi theo trường, liên kết chuyển form | Đăng nhập, tạo tài khoản |
| UI-13 | Cài đặt | Quản lý phiên và quyền | Thông tin tài khoản, ngôn ngữ, trạng thái quyền vị trí, trợ giúp quyền, đăng xuất | Mở cài đặt hệ thống, đăng xuất |
| UI-14 | Hỏi AI | Đặt câu hỏi trong ngữ cảnh | Chip ngữ cảnh địa điểm/chuyến đi, lịch sử hỏi đáp, ô nhập, nguồn dưới câu trả lời, trạng thái tải/lỗi | Gửi câu hỏi, mở nguồn, thử lại |

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
