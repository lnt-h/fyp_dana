# Research Protocol — Gonarra Usability Study

## Document control

| Field | Value |
|---|---|
| Document ID | GONARRA-RESEARCH-PROTOCOL |
| Version | 0.1 |
| Status | Draft — **pending OQ-004** (ethics approval / consent template) |
| Owner | Lê Ngọc Tấn Hiền, student author and study lead |
| Approver | trantrongminh, FYP mentor (OQ-001) — [Pending] |
| Date | 2026-11-04 |
| Parent plan | `TEST_PLAN.md` (TP-GONARRA-v0.1) §6.1.6, exit criteria §7.3 |
| Requirements | BR-023, BR-045, BR-046, FR-074, FR-077; MET-001, MET-002, MET-003, MET-013; NFR-018..NFR-021; AC-023, AC-045; RC-08 |
| Assumptions and risks | ASM-010 (retention to 2027-06-30), RSK-002 (free-tier AI terms), OQ-006 (baseline pre-task) |
| Replaces | Pre-rebuild `docs/RESEARCH.md` (in git history) |

Items marked **[Pending OQ-004]** depend on the mentor's answer about ethics approval and the consent template. If
the university supplies its own template, it replaces §9 and §10 and the content here is used to fill it. No session
runs before RC-08 is met (OQ-004 answered and the consent procedure approved).

## 1. Purpose and research questions

The study evaluates whether travellers can plan a short trip with Gonarra and find it usable, providing the FYP
evidence required by BR-023.

| ID | Question | Measure | Target |
|---|---|---|---|
| RQ-1 | Can participants produce and save a valid itinerary? | MET-001 planning task completion | ≥ 80% |
| RQ-2 | How quickly do participants reach a first proposal? | MET-002 median minutes from first request to first displayed proposal | ≤ 3 min |
| RQ-3 | How usable do participants find the app? | MET-003 mean System Usability Scale (SUS) score | ≥ 70 |
| RQ-4 (proposed, OQ-006) | Is planning with Gonarra faster than the participant's usual way? | Paired difference of baseline pre-task time vs. Gonarra time | Descriptive only |

The study is formative and descriptive. With 10–15 participants no statistical generalisation is claimed.

## 2. Design

| Element | Decision |
|---|---|
| Type | Task-based usability study, within-subject, single session per participant |
| Participants | 10–15 (BR-023, MET-013), at least 4 using Vietnamese and at least 4 using English (BR-045) |
| Window | Mid-January 2027: pilot on 2027-01-16 or 2027-01-17, sessions 2027-01-18 → 2027-01-29, all on or before 2027-01-31 (AC-023) |
| Setting | In person on an Android phone provided by the owner with the study build (remote fallback per OQ-115) |
| Build | Study release candidate that passed the exit criteria in `TEST_PLAN.md` §7.3 (RC-01..RC-05) |
| Language | The participant chooses VI or EN at the start; the whole session (forms, script, app) is in that language |
| Duration | About 45 minutes (55 with the optional baseline and HA-02 variant) |
| Facilitator | Lê Ngọc Tấn Hiền (observer and timekeeper) |

## 3. Participants

- Inclusion: adults aged 18 or over; use a smartphone regularly; have travelled to, or plan to travel to, at least
  one of Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Hội An or Huế; read Vietnamese or English well enough for the session.
- Exclusion: people who worked on Gonarra; people who tested pre-study builds.
- Recruitment: university and personal networks; no payment (zero budget, CON-001). Channel and wording confirmed
  under OQ-113 **[Pending OQ-004]**.
- Balance: recruitment continues until at least 4 participants per language have completed (BR-045).
- Each participant receives a pseudonymous code `P01`..`P15`, assigned in session order.

## 4. Materials and setup

- Android phone with the study build; Wi-Fi and 4G available; production backend (ADR-002).
- Pre-created study accounts `P01`..`P15` flagged as study accounts (FR-077). Participants do **not** sign in with
  personal accounts, so no personal identifier enters the service.
- The app's AI notice (FR-074) is shown before the first request, in the chosen language.
- Printed: information sheet and consent form (§9, §10), task cards (§5), SUS questionnaire (VI or EN version),
  observer sheet (§6). The Vietnamese SUS wording is the owner's translation, reviewed for meaning by a second
  bilingual reader (OQ-111); this is recorded as a limitation.
- Timer on the observer sheet (fallback for MET-002 if the study log is unavailable, OQ-013).
- No audio or video recording. Screen recording is not used **[Pending OQ-004: only if the mentor requires it, with an
  explicit opt-in box]**.

## 5. Tasks

Tasks follow the BRD operational scenarios. Each task card is printed in the participant's language and shows the
goal, not the steps.

| Task | Scenario | Goal shown to the participant | Success definition | Measures |
|---|---|---|---|---|
| T0 (optional, OQ-006) | Baseline | "Plan two days in Hội An using the tools you normally use (web search, maps, notes). Stop when you have a first day-by-day plan, or after 10 minutes." | First draft plan written down | Baseline time (RQ-4) |
| T1 | SC-01 | "Plan 2 relaxed days in Hội An focusing on the old town and food, starting on a date the facilitator gives you. Fix anything that does not fit and save the trip." | A valid itinerary is saved (Plan Health not blocked) | MET-001, MET-002, observations |
| T2 | SC-02 | "You are at a stop of your trip. Show a driver where you are going, then ask the app when the place closes." | Place card shown with Vietnamese address; Guide answer with source shown (or "insufficient evidence") | Completion, observations |
| T3 | SC-03 | "From your saved trip, look for a place to stay for the same dates." | Stay partner opens with Hội An and the trip dates | Completion, observations |
| T4 (optional) | HA-02 variant | "Keep one stop of day 2 fixed and get a new plan for day 2 only." | Locked stop unchanged; day 1 unchanged; participant decides whether to save | Completion, observations |

Notes:

- T2 is done with a typed question. If voice is not cut (DEC-003) the facilitator offers voice as an option; it is
  not required and is not measured.
- T4 runs only if lock/regeneration is not cut and time allows.
- Participants planning in Vietnamese may choose Huế instead of Hội An for T1 to match SC-02; the city is recorded.
- The order is fixed (T0 → T1 → T2 → T3 → T4) because T2 and T3 use the trip saved in T1.

## 6. Measures and data collected

| Data item | How | Linked to | Personal? |
|---|---|---|---|
| Participant code, interface language, request-submitted time, first-proposal-displayed time, Save outcome | Automatic study log (FR-077, API-032) | MET-001, MET-002, AC-045 | Pseudonymous; no request or question text, no account identifier (US-036) |
| Task success / failure, assists, errors, comments (no names) | Observer sheet | MET-001, qualitative findings | Pseudonymous |
| SUS answers (10 items, 1–5) | Paper questionnaire | MET-003 | Pseudonymous |
| Age band, travel frequency, prior use of travel apps | Short pre-task questions | Description of sample | Pseudonymous, banded |
| Baseline time (if T0 is run) | Observer timer | RQ-4 | Pseudonymous |
| Name and signature | Consent form only | AC-023 | Personal — kept separately (§8) |

Definitions:

- **MET-001** = participants who saved a valid itinerary in T1 ÷ participants who started T1.
- **MET-002** = median over participants of (first proposal displayed − first request submitted), from the study log;
  observer timing used where the log is missing (recorded per participant).
- **MET-003** = mean SUS score, using standard scoring (odd items: score − 1; even items: 5 − score; sum × 2.5).
- Results are reported overall and per language.

## 7. Session procedure (summary)

| Step | Time | Activity |
|---|---|---|
| 1 | 5 min | Welcome, information sheet, questions, consent (§9/§10). No consent → no session. |
| 2 | 3 min | Language choice, pre-task questions, assign code |
| 3 | 10 min | T0 baseline (optional, OQ-006) |
| 4 | 20 min | T1–T3 (and T4 if applicable), think-aloud encouraged, no help unless stuck for 2 minutes (counted as assist) |
| 5 | 5 min | SUS questionnaire |
| 6 | 5 min | Debrief, open comments, withdrawal reminder |

The full script in both languages is in §11.

## 8. Consent, privacy and data handling

| Topic | Rule |
|---|---|
| Consent | Written informed consent before any data is collected; participants may stop at any time without giving a reason |
| AI notice (RSK-002) | Participants are told that what they type into the planner and Guide is sent to Google's Gemini service under free-tier terms, which may allow Google to use the content to improve its services; that account identifiers, contact details and precise location are never sent (BR-046); and that they should not type personal information. The same notice appears in the app (FR-074) |
| Pseudonymity | All study data uses the code `Pnn`. The only link between code and name is the consent form |
| Study accounts | Pre-created; no personal email or phone; deleted after the study through account deletion (FR-071); the pseudonymous study logs are kept (data model §3.2, SET NULL) |
| Storage | Signed consent forms on paper in a locked place controlled by the owner (or as scans in an encrypted folder), separate from the study data. Study data (logs export, observer sheets, SUS) in an encrypted folder; not committed to git; only aggregated results enter the FYP report |
| Retention | Study data and consent forms kept until **2027-06-30** and then destroyed (ASM-010); deletion checked on 2027-07-01 (NFR-018) |
| Withdrawal | A participant may withdraw during the session or later by contacting the owner with their code, until **2027-06-30**. Their data is then deleted; figures already included in a submitted report cannot be recalled but no new analysis uses the data **[Pending OQ-004: confirm the withdrawal deadline]** |
| Access | Owner only; the mentor may see pseudonymous data and, if required by the university, consent forms |
| Cross-border | Gemini processes content outside Vietnam; the obligation is open in OQ-008 and disclosed in the consent form |
| Risks to participants | Minimal: about 45 minutes of time; possible frustration with tasks. No sensitive data is requested |
| Ethics approval | **[Pending OQ-004]** — whether formal approval is needed, from whom, and whether the university template must be used |

## 9. Consent form — English template **[Pending OQ-004]**

> **Participant information and consent — Gonarra usability study**
>
> **Study:** Evaluation of Gonarra, a bilingual travel-planning app, for the final-year project of Lê Ngọc Tấn Hiền,
> supervised by [mentor name and title — OQ-001], [university name]. Contact: [owner's study e-mail].
>
> **What you will do:** In one session of about 45 minutes you will use the app on a phone we provide to plan a short
> trip, look at a place, and look for a stay, then fill in a 10-question usability questionnaire. Optionally you will
> first plan the same trip in your usual way for up to 10 minutes.
>
> **What we collect:** a participant code (not your name), your chosen language, the times at which you requested and
> received a trip proposal, whether you saved the trip, the facilitator's notes, your questionnaire answers and a few
> background questions (age band, travel habits). The app account you use is a study account, not your own. Nothing
> is audio- or video-recorded.
>
> **AI service:** What you type into the planner or the Guide is sent to Google's Gemini AI service, under free-tier
> terms that may allow Google to use this content to improve its services, and it may be processed outside Vietnam.
> Your name, contact details and precise location are never sent. Please do not type personal information.
>
> **Your rights:** Taking part is voluntary. You can stop at any time without giving a reason. You can withdraw your
> data until 30 June 2027 by e-mailing the contact above with your participant code; results already submitted in the
> report cannot be recalled.
>
> **Storage:** Study data is pseudonymous, stored encrypted, used only for this project, and deleted on 30 June 2027.
> This form is stored separately from the study data and destroyed on the same date.
>
> **Consent** (tick each box):
>
> - [ ] I have read this information and had the chance to ask questions.
> - [ ] I understand that what I type is sent to an external AI service as described above.
> - [ ] I agree that my pseudonymous data is used in the final-year project report.
> - [ ] I am 18 years old or over.
>
> Name: ______________________ Signature: ______________________ Date: ____ / ____ / 2027
>
> Participant code (filled in by the facilitator): P____
>
> Facilitator: Lê Ngọc Tấn Hiền — Signature: ______________________

## 10. Consent form — Vietnamese template (Phiếu đồng ý tham gia) **[Pending OQ-004]**

> **Thông tin cho người tham gia và phiếu đồng ý — Nghiên cứu khả năng sử dụng ứng dụng Gonarra**
>
> **Nghiên cứu:** Đánh giá Gonarra, ứng dụng lập kế hoạch du lịch song ngữ, thuộc đồ án tốt nghiệp của Lê Ngọc Tấn
> Hiền, do [họ tên và học hàm của giảng viên hướng dẫn — OQ-001] hướng dẫn, [tên trường]. Liên hệ: [e-mail nghiên
> cứu của sinh viên].
>
> **Bạn sẽ làm gì:** Trong một buổi khoảng 45 phút, bạn dùng ứng dụng trên điện thoại do chúng tôi cung cấp để lập kế
> hoạch một chuyến đi ngắn, xem thông tin một địa điểm và tìm chỗ ở, sau đó trả lời bảng hỏi 10 câu về mức độ dễ sử
> dụng. Bạn có thể (không bắt buộc) lập kế hoạch cho cùng chuyến đi theo cách bạn vẫn thường làm, tối đa 10 phút.
>
> **Dữ liệu được thu thập:** mã người tham gia (không phải tên của bạn), ngôn ngữ bạn chọn, thời điểm bạn gửi yêu cầu
> và nhận đề xuất lịch trình, việc bạn có lưu chuyến đi hay không, ghi chú của người điều phối, câu trả lời bảng hỏi
> và vài câu hỏi chung (nhóm tuổi, thói quen du lịch). Tài khoản dùng trong buổi thử là tài khoản nghiên cứu, không
> phải tài khoản của bạn. Buổi thử không ghi âm, không quay video.
>
> **Dịch vụ AI:** Nội dung bạn nhập vào phần lập kế hoạch hoặc phần Hướng dẫn (Guide) được gửi tới dịch vụ AI Gemini
> của Google theo điều khoản gói miễn phí; điều khoản này có thể cho phép Google dùng nội dung đó để cải thiện dịch vụ,
> và nội dung có thể được xử lý ở ngoài Việt Nam. Họ tên, thông tin liên lạc và vị trí chính xác của bạn không bao giờ
> được gửi đi. Vui lòng không nhập thông tin cá nhân.
>
> **Quyền của bạn:** Việc tham gia là tự nguyện. Bạn có thể dừng bất cứ lúc nào mà không cần nêu lý do. Bạn có thể rút
> dữ liệu của mình đến hết ngày 30/06/2027 bằng cách gửi e-mail tới địa chỉ liên hệ ở trên kèm mã người tham gia; các
> kết quả đã nộp trong báo cáo thì không thể thu hồi.
>
> **Lưu trữ:** Dữ liệu nghiên cứu được ẩn danh hóa bằng mã, lưu trữ có mã hóa, chỉ dùng cho đồ án này và bị xóa vào
> ngày 30/06/2027. Phiếu này được lưu riêng với dữ liệu nghiên cứu và được hủy cùng ngày.
>
> **Đồng ý** (đánh dấu từng ô):
>
> - [ ] Tôi đã đọc thông tin trên và đã có cơ hội đặt câu hỏi.
> - [ ] Tôi hiểu rằng nội dung tôi nhập được gửi tới một dịch vụ AI bên ngoài như mô tả ở trên.
> - [ ] Tôi đồng ý cho phép dùng dữ liệu đã ẩn danh của tôi trong báo cáo đồ án tốt nghiệp.
> - [ ] Tôi từ đủ 18 tuổi trở lên.
>
> Họ tên: ______________________ Chữ ký: ______________________ Ngày: ____ / ____ / 2027
>
> Mã người tham gia (người điều phối ghi): P____
>
> Người điều phối: Lê Ngọc Tấn Hiền — Chữ ký: ______________________

## 11. Session script

The facilitator reads the script in the participant's chosen language. Text in brackets is an instruction to the
facilitator, not read aloud.

### 11.1 English

1. **Welcome.** "Thank you for coming. I'm testing an app, not you — there are no wrong answers. If something is
   confusing, that is useful for me to know. The session takes about 45 minutes and you can stop at any time."
2. **Consent.** [Give the information sheet and consent form (§9). Answer questions. Collect the signed form. If not
   signed, thank the person and end.] [Assign the next code `Pnn`; sign in the matching study account.]
3. **Background.** "Three quick questions: which age band are you in — 18–24, 25–34, 35–44, 45 or over? How many trips
   within Vietnam did you take in the last 12 months? Which apps do you usually use to plan trips?"
4. **Baseline (optional, T0 — only if OQ-006 approves it).** "Please plan two days in Hội An the way you normally
   would — any website, map or notes app on your own phone. Tell me when you have a first day-by-day plan. I'll stop
   you after 10 minutes." [Start timer at "go"; stop when the participant says done or at 10:00.]
5. **Think-aloud.** "While you use the app, please say what you are looking for and what you expect to happen. I won't
   help unless you are stuck; if you want to give up a task, just say so."
6. **T1.** [Hand the T1 card; give the start date.] "Please plan 2 relaxed days in Hội An focusing on the old town and
   food, starting on this date. Fix anything that doesn't fit, and save the trip when you're happy." [Note the time of
   the first request and of the first proposal if the log fails; note assists after 2 minutes stuck.]
7. **T2.** [Hand the T2 card.] "Imagine you are standing outside one of your stops. Show me the screen you would show a
   taxi driver, then ask the app when that place closes."
8. **T3.** [Hand the T3 card.] "From your saved trip, look for a place to stay for the same dates." [Success when the
   partner page opens with Hội An and the dates; the participant does not book anything.]
9. **T4 (optional).** "Choose one stop on day 2 that you want to keep, keep it fixed, and get a new plan for day 2
   only. Decide whether you want to save it."
10. **SUS.** [Hand the English SUS form.] "Please answer these 10 statements about the app you just used."
11. **Debrief.** "What did you like most? What was most confusing? Anything else?" "Thank you. Your participant code
    is Pnn. If you want to withdraw your data before 30 June 2027, e-mail me with this code."
12. [After the participant leaves: complete the observer sheet; check the study log entry for the code; sign the
    study account out.]

### 11.2 Tiếng Việt

1. **Chào mừng.** "Cảm ơn bạn đã đến. Mình đang thử nghiệm ứng dụng, không phải kiểm tra bạn — không có câu trả lời
   nào là sai. Chỗ nào khó hiểu thì đó chính là điều mình cần biết. Buổi thử kéo dài khoảng 45 phút và bạn có thể
   dừng bất cứ lúc nào."
2. **Đồng ý tham gia.** [Đưa phiếu thông tin và phiếu đồng ý (§10). Trả lời câu hỏi. Nhận phiếu đã ký. Nếu không ký,
   cảm ơn và kết thúc.] [Gán mã tiếp theo `Pnn`; đăng nhập tài khoản nghiên cứu tương ứng.]
3. **Thông tin chung.** "Mình hỏi nhanh ba câu: bạn thuộc nhóm tuổi nào — 18–24, 25–34, 35–44 hay từ 45 trở lên? Trong
   12 tháng qua bạn đi du lịch trong nước bao nhiêu chuyến? Bạn thường dùng ứng dụng nào để lên kế hoạch du lịch?"
4. **Nhiệm vụ đối chứng (không bắt buộc, T0 — chỉ khi OQ-006 được chấp thuận).** "Bạn hãy lên kế hoạch hai ngày ở Hội
   An theo cách bạn vẫn thường làm — dùng bất kỳ trang web, bản đồ hay ứng dụng ghi chú nào trên điện thoại của bạn.
   Khi có kế hoạch sơ bộ theo từng ngày thì báo mình. Mình sẽ dừng sau 10 phút." [Bấm giờ khi bắt đầu; dừng khi người
   tham gia báo xong hoặc tới 10:00.]
5. **Nói to suy nghĩ.** "Trong lúc dùng ứng dụng, bạn hãy nói ra bạn đang tìm gì và bạn nghĩ điều gì sẽ xảy ra. Mình
   sẽ không giúp trừ khi bạn bị kẹt; nếu muốn bỏ qua nhiệm vụ nào, bạn cứ nói."
6. **T1.** [Đưa thẻ T1; cho ngày bắt đầu.] "Bạn hãy lên kế hoạch 2 ngày thư thả ở Hội An, tập trung vào phố cổ và ẩm
   thực, bắt đầu từ ngày này. Chỗ nào không hợp lý thì sửa lại, và lưu chuyến đi khi bạn thấy ổn." [Bạn nào muốn có
   thể chọn Huế thay cho Hội An; ghi lại thành phố đã chọn.] [Ghi thời điểm gửi yêu cầu đầu tiên và thời điểm thấy đề
   xuất đầu tiên nếu nhật ký lỗi; ghi lại lần hỗ trợ khi bị kẹt quá 2 phút.]
7. **T2.** [Đưa thẻ T2.] "Giả sử bạn đang đứng trước một điểm đến trong chuyến đi. Hãy mở màn hình bạn sẽ đưa cho tài
   xế taxi xem, rồi hỏi ứng dụng xem nơi đó mấy giờ đóng cửa."
8. **T3.** [Đưa thẻ T3.] "Từ chuyến đi đã lưu, bạn hãy tìm chỗ ở cho đúng những ngày đó." [Thành công khi trang đối tác
   mở ra với thành phố và ngày của chuyến đi; người tham gia không đặt phòng.]
9. **T4 (không bắt buộc).** "Bạn chọn một điểm ở ngày 2 mà bạn muốn giữ, cố định điểm đó, rồi tạo lại kế hoạch chỉ cho
   ngày 2. Bạn tự quyết định có lưu hay không."
10. **SUS.** [Đưa bảng hỏi SUS tiếng Việt.] "Bạn hãy trả lời 10 nhận định này về ứng dụng bạn vừa dùng."
11. **Kết thúc.** "Bạn thích điều gì nhất? Điều gì khó hiểu nhất? Bạn còn góp ý gì không?" "Cảm ơn bạn. Mã người tham
    gia của bạn là Pnn. Nếu muốn rút dữ liệu trước ngày 30/06/2027, bạn gửi e-mail cho mình kèm mã này."
12. [Sau khi người tham gia rời đi: hoàn thành phiếu quan sát; kiểm tra bản ghi nhật ký nghiên cứu theo mã; đăng xuất
    tài khoản nghiên cứu.]

## 12. Analysis and reporting

- Report n per language, MET-001 (with 95% interval stated as indicative only), MET-002 median and range, MET-003 mean
  and standard deviation, overall and per language; task success for T2–T4.
- RQ-4 (if T0 approved): per-participant difference baseline − Gonarra time to first plan, reported descriptively.
- Qualitative findings: issues grouped by screen and severity; each issue that reveals a defect becomes `DEF-xxx`.
- Deviations (log missing, task skipped, build issue) are listed per participant.
- Results go into the test summary report (`TEST_PLAN.md` §9) by 2027-01-31 and feed MET-001..MET-003, MET-013,
  AC-023 and AC-045 (cases TC-213, TC-214, TC-241..TC-243 in `TEST_CASES.md`).

## 13. Pilot

One pilot session with a person who is not counted as a participant (2027-01-16 or 2027-01-17) checks timing, task
wording in both languages, the study log (US-036) and the SUS forms. Changes after the pilot are recorded in this
document's change history before the first counted session.

## 14. Dependencies and open items

| ID | Item | Status | Owner | Needed by |
|---|---|---|---|---|
| OQ-004 | Ethics approval and consent template | Open — **blocks the study** (RC-08) | Lê Ngọc Tấn Hiền (ask mentor) | 2026-11-11 |
| OQ-006 | Baseline pre-task (T0) | Open — proposed design in §5 | Lê Ngọc Tấn Hiền | 2026-11-15 |
| OQ-008 | Cross-border data obligations | Open — disclosed in consent | Lê Ngọc Tấn Hiền | per BRD |
| OQ-013 | Observer-timing fallback for MET-002 | Per PRD | Lê Ngọc Tấn Hiền | per PRD |
| OQ-111 | Second reviewer for the Vietnamese SUS wording and EN content | Open | trantrongminh | 2026-12-08 |
| OQ-113 | Recruitment channel and compensation | Open | Lê Ngọc Tấn Hiền | 2026-12-15 |
| OQ-115 | In person vs remote sessions | Open | Lê Ngọc Tấn Hiền | 2026-12-15 |

## 15. Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Study lead | Lê Ngọc Tấn Hiền | [Pending] | — |
| Mentor | trantrongminh | [Pending] | — |
| Ethics body (if required by OQ-004) | [Pending OQ-004] | [Pending] | — |
