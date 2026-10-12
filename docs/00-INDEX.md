# Danang TourGuide — Bộ tài liệu kỹ thuật và đồ án

Version 1.2 | 2026-10-12 | Design baseline for review

## Mục đích và phạm vi

Bộ tài liệu xác định vấn đề, yêu cầu, thiết kế, hợp đồng dữ liệu/API, kế hoạch thực hiện và phương pháp kiểm chứng trước khi xây dựng ứng dụng. Phạm vi P0: Explore, lịch trình AI có thể chỉnh sửa, bản đồ, GPS foreground/xác nhận thủ công, audio người thật và hỏi đáp RAG có nguồn. Tài khoản và Saved hỗ trợ lưu trữ riêng tư. Camera, STT và Google login là P1 chưa cam kết; cá nhân hóa bằng ảnh/Travel DNA thuộc Future.

## Kiểm soát tài liệu

Owner: sinh viên phát triển đồ án; tên chưa cung cấp. Technical reviewer và giảng viên hướng dẫn: chưa xác định trong hồ sơ. AI hỗ trợ biên soạn; người thực hiện chịu trách nhiệm hiểu và kiểm chứng nội dung.
Trạng thái **design baseline for review** nghĩa là bộ thiết kế làm việc đã được ghi thành tài liệu, chưa phải phê duyệt học thuật hoặc bằng chứng hệ thống chạy đúng. Phạm vi P0 được người dùng chọn; quyết định thiết kế của bộ docs và đề xuất cần thử nghiệm được phân biệt tại [Decisions](09-Project-Decisions.md). Không mặc định mọi giá trị đề xuất đã được duyệt.
Version 1.2 thay thế 1.1: chuẩn hóa quyền sở hữu nội dung, sửa căn cứ khảo sát, bổ sung quy tắc trạng thái/API, hợp nhất quy trình đánh giá và rút các đoạn quản lý lặp. Giữ tên file hiện tại; không tạo ZIP hoặc bộ bản sao. Đây là điều chỉnh cách tổ chức thư mục theo yêu cầu người dùng, khác cách chia thư mục phase trong SOP; không phải khẳng định tuân thủ nguyên trạng toàn bộ SOP.

## Tài liệu sở hữu nội dung

| Tài liệu | Nội dung chính và trách nhiệm |
|---|---|
| [10-BRD](10-BRD.md) | Vấn đề, bên liên quan, mục tiêu và giá trị nghiệp vụ |
| [01-PRD](01-PRD.md) | Phạm vi; FR/NFR; business rules; tiêu chí chấp nhận |
| [11-User Stories](11-User-Stories.md) | Kết quả người dùng và Given/When/Then |
| [03-Use Cases](03-Use-Cases.md) | Tác nhân, điều kiện, luồng chính, ngoại lệ và kết quả |
| [02-SAD](02-SAD.md) | Kiến trúc, 4+1 views, ranh giới và phương án triển khai |
| [12-Blueprint](12-Blueprint.md) | Thuật toán, bảng trạng thái, giao dịch và xử lý đồng thời |
| [04-Sequences](04-Sequence-Diagrams.md) | Catalogue, diễn giải và liên kết sơ đồ tuần tự |
| [05-Database](05-Database-Design.md), [DDL](database.sql) | Thiết kế dữ liệu và ràng buộc vật lý dự kiến |
| [06-API](06-API-Design.md), [OpenAPI](openapi.json) | Ngữ nghĩa API và schema máy đọc được |
| [07-UI/UX](07-UI-UX-Design.md), [Wireframes](UI_UX_design/wireframes.html) | Màn hình, component, trạng thái, accessibility |
| [15-Security/Privacy](15-Security-Privacy.md) | Threat model, phiên đăng nhập và vòng đời dữ liệu |
| [16-Data Curation](16-Data-Curation.md) | Nguồn, dữ liệu POI, quyền hình/audio và xuất bản RAG |
| [13-Development Plan](13-Development-Plan.md) | Mốc, backlog, phụ thuộc, ước lượng và rủi ro |
| [09-Decisions](09-Project-Decisions.md) | Quyết định, lý do, cấu hình đề xuất và thông tin chưa chốt |
| [14-Traceability](14-Traceability.md) | Mục tiêu → yêu cầu → thiết kế → task → test |
| [08-Test Plan](08-Test-Plan.md) | Chiến lược, test case, đánh giá AI/GPS/UAT và ghi bằng chứng |
| [17-Research/Academic](17-Research-and-Academic-Plan.md) | Căn cứ nghiên cứu, phương pháp và cấu trúc báo cáo |
| [18-Document Review](18-Document-Review.md) | Hồ sơ kiểm tra nội bộ và giới hạn kiểm chứng |

Đọc BRD → PRD/stories → use cases → SAD/Blueprint → DB/API/UI → security/curation → plan/test/traceability. Research được thực hiện song song với xác minh vấn đề và được cập nhật khi có bằng chứng.
Một thông tin có một nơi sở hữu; tài liệu khác liên kết hoặc mô tả tác động. Thay đổi yêu cầu phải cập nhật truy vết, schema, giao diện và test liên quan trong cùng lượt chỉnh sửa. ID đã cấp được giữ ổn định; P1 không tính vào nghiệm thu P0.

## Thiết kế và bằng chứng

| Loại nội dung | Trạng thái hiện tại |
|---|---|
| Phạm vi sản phẩm | P0 được chọn; rubric/đề cương đã duyệt chưa cung cấp |
| Yêu cầu, thuật toán, hợp đồng | Đã soạn cho review; trial cần thiết có owner/gate |
| Phiên bản SDK/ORM/model; GPS, ngân sách, lịch | Chờ quyết định/trial trong Decisions |
| Nguồn nghiên cứu | Nguồn công khai đã tham khảo ghi tại Research; không thay thế rubric của trường |
| Dữ liệu POI, quyền media, khảo sát/UAT | Chưa thu thập hoặc xác minh |
| Mã ứng dụng, migration, kết quả test/deploy | Chưa triển khai; không có kết quả runtime |
| Kiểm tra cấu trúc docs | Kết quả và giới hạn tại Document Review |

Hoàn thiện thiết kế trước code không yêu cầu bịa kết quả thực nghiệm. Feasibility spike là bước xác minh tham số/khả năng tích hợp; kết quả phải được đưa ngược vào thiết kế trước khi triển khai phần phụ thuộc.

## Sơ đồ

| Diagram | Editable source | Preview |
|---|---|---|
| Logical | [logical-view.drawio](diagrams/logical-view.drawio) | [SVG](diagrams/previews/logical-view.svg) |
| Process | [process-view.drawio](diagrams/process-view.drawio) | [SVG](diagrams/previews/process-view.svg) |
| Development | [development-view.drawio](diagrams/development-view.drawio) | [SVG](diagrams/previews/development-view.svg) |
| Physical | [physical-view.drawio](diagrams/physical-view.drawio) | [SVG](diagrams/previews/physical-view.svg) |
| Scenarios / use cases | [scenarios-view.drawio](diagrams/scenarios-view.drawio) | [SVG](diagrams/previews/scenarios-view.svg) |
| Planning sequence | [sequence-planning.drawio](diagrams/sequence-planning.drawio) | [SVG](diagrams/previews/sequence-planning.svg) |
| Editing sequence | [sequence-edit.drawio](diagrams/sequence-edit.drawio) | [SVG](diagrams/previews/sequence-edit.svg) |
| Arrival/audio sequence | [sequence-arrival.drawio](diagrams/sequence-arrival.drawio) | [SVG](diagrams/previews/sequence-arrival.svg) |
| RAG sequence | [sequence-rag.drawio](diagrams/sequence-rag.drawio) | [SVG](diagrams/previews/sequence-rag.svg) |
| Rich Picture | [rich-picture.drawio](diagrams/rich-picture.drawio) | [SVG](diagrams/previews/rich-picture.svg) |

.drawio là nguồn chỉnh sửa; SVG là bản xem/nhúng. Không duy trì thêm một bản Mermaid cho cùng sơ đồ tuần tự. ERD trong Database và sơ đồ context trong SAD có mục đích riêng. Diagram physical thể hiện phương án AWS cần xác minh chi phí, không mô tả hệ thống đã triển khai. Import/kiểm tra hình ảnh theo công cụ đích vẫn là bước review được ghi rõ trong hồ sơ.

## Cách dùng cho báo cáo tốt nghiệp

Bộ docs là hồ sơ kỹ thuật, không phải 19 chương báo cáo. Báo cáo chính trình bày vấn đề và mục tiêu, nghiên cứu, yêu cầu, phương pháp, quyết định thiết kế quan trọng, triển khai khi có, kiểm thử/đánh giá và hạn chế. Đưa hợp đồng API đầy đủ, DDL, chi tiết test, nguồn sơ đồ và hồ sơ review vào phụ lục khi template cho phép. [Research](17-Research-and-Academic-Plan.md) ánh xạ nội dung sang bằng chứng cần nộp.
