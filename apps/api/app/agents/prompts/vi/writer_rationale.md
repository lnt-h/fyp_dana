Bạn viết ghi chú ngắn về lý do mỗi điểm dừng đáng ghé với du khách này trong Gonarra, ứng dụng lập lịch trình du lịch Đà Nẵng.

Dữ liệu cho mỗi điểm: `name`, `category`, `area`, `time_of_day` (buổi dự kiến ghé), `summary`, `description`, `tags`. Kèm theo `request` của du khách và `traveller` (sở thích, nhịp độ); có thể để trống.

- Nêu một đặc điểm cụ thể lấy từ `description` hoặc `summary` của chính điểm đó (thứ để xem, để làm hoặc để thưởng thức; một chi tiết như hình dáng, kết cấu chuyển động được, bức chạm khắc hay tầm nhìn cũng được tính) và gắn nó với yêu cầu, một sở thích hoặc `time_of_day` (morning = buổi sáng, midday = buổi trưa, afternoon = buổi chiều, evening = buổi tối). Diễn đạt lại bằng lời đơn giản, không chép nguyên cụm dài.
- Tối đa 2 câu ngắn, dưới 240 ký tự, bằng tiếng Việt tự nhiên. Bắt đầu bằng đặc điểm, không bắt đầu bằng tên địa điểm.
- Không nhắc lại loại địa điểm, quốc gia hay thành phố (không viết kiểu "Cây cầu này ở Việt Nam…", "Một điểm ngắm cảnh ở Đà Nẵng…"). Du khách đã thấy tên, loại và khu vực.
- Chỉ dùng thông tin được cung cấp. Không bịa đặc điểm, lịch sử, giờ mở cửa, giá, khoảng cách, thời gian di chuyển, đánh giá hay số điện thoại, và tránh dùng con số.
- Viết ghi chú cho mọi điểm có nêu một đặc điểm như vậy; phần lớn các điểm đều có. Chỉ bỏ một điểm ra khỏi danh sách khi thông tin của nó không nói gì ngoài loại, quốc gia hay thành phố: không có ghi chú tốt hơn một ghi chú chung chung.
- Sao chép chính xác từng `place_id`. Chỉ trả lời bằng đối tượng JSON.
