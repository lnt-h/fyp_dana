# DaNavi — Bộ tài liệu kỹ thuật và đồ án

Version 1.3 | 2026-10-19 | Design baseline for review

## Mục đích và phạm vi

Bộ tài liệu xác định sản phẩm mobile English-first dành cho khách quốc tế lần đầu hoặc ít quen Đà Nẵng. Flow P0: Welcome → Home → Explore/Detail → one-day preferences → login gate khi Generate → AI Preview → **Save & customize** → Edit → Route/Trip Ready → external Google/Apple Maps directions → Active Trip → **I've arrived** hoặc foreground dwell → human English Audio/Ask with sources → Completed.

Guest được xem Explore, Detail và nghe audio preview. Save, Ask và Generate cần tài khoản. P0 dùng một ngày, car/ride-hailing, start point bằng map pin/current location/preset; không tự xây turn-by-turn navigation, background GPS, TTS, offline maps hoặc offline routing. P0 có read-only essentials cache, xoá tài khoản, 15–20 POI thuộc Culture/Beach/Food/Nature và năm audio người thật. Camera, STT và Google login là P1 chưa cam kết.

## Kiểm soát tài liệu

Owner: sinh viên phát triển đồ án; technical reviewer và giảng viên hướng dẫn chưa được xác định trong hồ sơ. AI hỗ trợ biên soạn; người thực hiện chịu trách nhiệm hiểu, kiểm chứng và phê duyệt nội dung.

Trạng thái **design baseline for review** nghĩa là tài liệu đã được đồng bộ để review, không có nghĩa ứng dụng, migration, API, GPS, AI, deployment hay nghiên cứu người dùng đã chạy. Version 1.3 thay thế 1.2 về product direction và giữ lịch sử quyết định: D-10/D-12, TC-36 và UI-10 được đánh dấu superseded/retired, không tái sử dụng ID.

`docs/openapi.json` là hợp đồng API chính thức có kiểm soát phiên bản nên vẫn được Git theo dõi. `.gitignore` chỉ loại các bản contract sinh tạm như `openapi.generated.*`, build output, cache, log, editor và secret cục bộ.

## Tài liệu sở hữu nội dung

| Tài liệu | Nội dung chính và trách nhiệm |
|---|---|
| [10-BRD](10-BRD.md) | Vấn đề, persona, bên liên quan, mục tiêu và giá trị nghiệp vụ |
| [01-PRD](01-PRD.md) | P0/P1/Future, FR/NFR, business rules và nghiệm thu |
| [11-User Stories](11-User-Stories.md) | Kết quả người dùng và Given/When/Then |
| [03-Use Cases](03-Use-Cases.md) | Tác nhân, điều kiện, flow chính, ngoại lệ và kết quả |
| [02-SAD](02-SAD.md) | Kiến trúc, boundaries, 4+1 views, deployment/recovery option |
| [12-Blueprint](12-Blueprint.md) | Thuật toán, state, transaction, idempotency, cache và resume |
| [04-Sequences](04-Sequence-Diagrams.md) | Catalogue và semantics của sequence diagrams |
| [05-Database](05-Database-Design.md), [DDL](database.sql) | Data model, alias/translation provenance, constraint và cascade |
| [06-API](06-API-Design.md), [OpenAPI](openapi.json) | Auth, versioning, request/response và canonical machine-readable contract |
| [07-UI/UX](07-UI-UX-Design.md), [Wireframes](UI_UX_design/wireframes.html) | Canonical screen inventory, states, navigation, tokens và editable concept frames |
| [15-Security/Privacy](15-Security-Privacy.md) | Threat model, guest/auth boundary, deletion/retention, cache/privacy |
| [16-Data Curation](16-Data-Curation.md) | English/local aliases, nguồn, dịch, media/offline rights và RAG publication |
| [13-Development Plan](13-Development-Plan.md) | Mốc, TASK-01–29, phụ thuộc, ước lượng sơ bộ và rủi ro |
| [09-Decisions](09-Project-Decisions.md) | D-01–34, quyết định được chọn và open inputs |
| [14-Traceability](14-Traceability.md) | BIZ → FR → story/use case → module/data/API/UI → task/test |
| [08-Test Plan](08-Test-Plan.md) | TC-01–45, held-out RAG, GPS/audio fieldwork và UAT |
| [17-Research/Academic](17-Research-and-Academic-Plan.md) | RQ, tuyển participant, nguồn đã đọc, competitor evidence và report mapping |
| [18-Document Review](18-Document-Review.md) | Các kiểm tra thật sự đã chạy, kết quả và giới hạn |

[design.md](../design.md) và [19-App-Feature-Screens](19-App-Feature-Screens.md) là retirement stubs; không còn sở hữu UI requirements hoặc screen IDs. Nguồn UI chính thức là 07-UI-UX. Curator CLI là workflow kỹ thuật, không phải màn admin mới.

Thứ tự đọc khuyến nghị: BRD → PRD/stories → use cases → SAD/Blueprint → DB/API/UI → security/curation → plan/test/traceability. Research chạy song song với xác minh problem/market và phải cập nhật yêu cầu nếu bằng chứng mâu thuẫn.

## Trạng thái thiết kế và bằng chứng

| Loại nội dung | Trạng thái hiện tại |
|---|---|
| Product direction v1.3 | Đã chọn để review; chưa phải approval của supervisor |
| Yêu cầu, thuật toán, DB/API/UI | Đã đồng bộ trong docs; implementation vẫn NOT STARTED |
| Figma/wireframes | Concept screens hiện có; cần native implementation/accessibility review sau này |
| Provider/SDK/ORM/model/version | Chờ feasibility trial và pin version |
| POI, bản dịch, audio/media rights | Chưa thu thập/xác minh; target 15–20 POI và năm audio |
| Research/UAT | Chưa tuyển/thu thập; target persona là English-speaking international visitor |
| Test/deployment | Không có runtime result; mọi test active là NOT RUN |
| Research nguồn web v1.3 | Mindtrip, GuideAlong và policy account/guest được đọc trực tiếp ngày 2026-10-19; không phải benchmark app |

## Sơ đồ

| Diagram | Editable source | Preview |
|---|---|---|
| Logical | [drawio](diagrams/logical-view.drawio) | [SVG](diagrams/previews/logical-view.svg) |
| Process | [drawio](diagrams/process-view.drawio) | [SVG](diagrams/previews/process-view.svg) |
| Development | [drawio](diagrams/development-view.drawio) | [SVG](diagrams/previews/development-view.svg) |
| Physical | [drawio](diagrams/physical-view.drawio) | [SVG](diagrams/previews/physical-view.svg) |
| Scenarios / use cases | [drawio](diagrams/scenarios-view.drawio) | [SVG](diagrams/previews/scenarios-view.svg) |
| Planning / guest gate | [drawio](diagrams/sequence-planning.drawio) | [SVG](diagrams/previews/sequence-planning.svg) |
| Editing | [drawio](diagrams/sequence-edit.drawio) | [SVG](diagrams/previews/sequence-edit.svg) |
| Start/cache/handoff/arrival/audio | [drawio](diagrams/sequence-arrival.drawio) | [SVG](diagrams/previews/sequence-arrival.svg) |
| Single-turn RAG | [drawio](diagrams/sequence-rag.drawio) | [SVG](diagrams/previews/sequence-rag.svg) |
| Rich Picture | [drawio](diagrams/rich-picture.drawio) | [SVG](diagrams/previews/rich-picture.svg) |

`.drawio` là nguồn chỉnh sửa; SVG là preview review/report. Physical view chỉ là phương án triển khai cần xác minh chi phí/host, không mô tả hệ thống đã deploy.

## Cách dùng cho báo cáo tốt nghiệp

Bộ docs là hồ sơ kỹ thuật, không phải 19 chương báo cáo. Báo cáo chính nên trình bày vấn đề/persona, research và related systems, requirements, lựa chọn thiết kế quan trọng, implementation thực tế, evaluation thực tế và limitations. OpenAPI, DDL, test detail, diagrams và review record có thể đưa vào appendix theo template chính thức. Không đưa số đo, participant response, quyền media hoặc kết quả test chưa thu thập vào báo cáo như dữ kiện đã có.
