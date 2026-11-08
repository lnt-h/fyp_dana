# Research Protocol — Gonarra Comparative User Study

| Field | Value |
|---|---|
| Version / date | 1.0 / 2026-11-09 (0.1 of 2026-11-04 was a single-arm usability study for five cities; kept at tag `docs-sdlc-full`) |
| Status | Draft — **pending OQ-004** (ethics approval / consent template) and OQ-130 (baseline protocol) |
| Owner | Lê Ngọc Tấn Hiền, student author and study lead |
| Approver | FYP mentor — [Pending] |
| Parent plan | [TEST_PLAN.md](TEST_PLAN.md) §6 (DEC-020); exit and entry criteria §8 |
| Measures | MET-001, MET-002, MET-003, MET-014; trust rating; trust-label noticed |
| Related | FR-074 (AI notice), FR-077 (study log), BR-046 (redaction), OQ-004, OQ-008, OQ-111, OQ-113, OQ-128, OQ-130, OQ-131, RSK-013 |

Items marked **[Pending OQ-004]** depend on the mentor's answer about ethics approval and the consent template. If
the university supplies its own template, it replaces §6 and §7 and the content here is used to fill it. No session
runs before OQ-004 is answered and the consent procedure approved.

## 1. Purpose and questions

The study compares planning a short Đà Nẵng trip with Gonarra against a general-purpose AI chatbot (ChatGPT or
Gemini), as required by DEC-020. It is formative and descriptive: with 10–15 participants no statistical
generalisation is claimed.

| ID | Question | Measure |
|---|---|---|
| RQ-1 | Do Gonarra itineraries contain fewer factual errors than chatbot itineraries? | MET-014 errors per planned day (closed place, wrong hours, non-existent place), both arms |
| RQ-2 | Do participants trust the two itineraries differently, and do they notice the trust labels? | Trust rating 1–5 per itinerary; "did you notice the labels?" after the Gonarra arm |
| RQ-3 | Can participants produce and save a valid itinerary with Gonarra, and how fast? | MET-001 (≥ 80%), MET-002 (median ≤ 3 min) |
| RQ-4 | How usable is Gonarra? | MET-003 mean SUS (≥ 70) |

## 2. Design

| Element | Decision |
|---|---|
| Type | Within-subject comparison, one session per participant, two arms: Gonarra (phone) and baseline chatbot (laptop) |
| Prompts | Two fixed Đà Nẵng prompts, 2 days each, with fixed dates: **P-A** Hội An area (Old Town and food), **P-B** central Đà Nẵng. Proposed: dates chosen so that at least one calendar rule applies (weekly closure or lantern night). Text identical in both arms; VI and EN versions; final wording fixed after the pilot |
| Assignment | Each participant does one prompt per arm. Four orders rotate in session order: Gonarra/P-A then baseline/P-B; baseline/P-A then Gonarra/P-B; Gonarra/P-B then baseline/P-A; baseline/P-B then Gonarra/P-A |
| Baseline | ChatGPT or Gemini, owner-provided account, model version recorded per session; participant pastes the prompt and may ask follow-ups; final itinerary copied as text and a screenshot archived (OQ-130) |
| Participants | 10–15 adults, ≥ 4 using VI and ≥ 4 using EN |
| Window | Pilot 2027-01-16 or 2027-01-17; sessions 2027-01-18 → 2027-01-29, spread over ≥ 2 days so free quotas are not exhausted (RSK-013) |
| Setting | In person; owner-provided phone with the study build against the staging environment (measured router, never estimated legs, OQ-132); laptop for the baseline |
| Language | Chosen at the start; forms, script, prompts and app all in that language |
| Duration | About 50 minutes |
| Facilitator | Lê Ngọc Tấn Hiền (observer and timekeeper) |

`WEB_UNVERIFIED` stops may appear in the Gonarra arm; saving such a plan needs the in-app acknowledgement (OQ-128).

## 3. Participants and materials

- Inclusion: adults aged 18 or over; use a smartphone regularly; read Vietnamese or English well enough for the session.
- Exclusion: people who worked on Gonarra or tested pre-study builds.
- Recruitment: university and personal networks; no payment (OQ-113 **[Pending OQ-004]**). Continue until ≥ 4 per language.
- Codes `P01`..`P15` in session order. Pre-created study accounts flagged as study accounts (FR-077); participants never
  sign in with personal accounts.
- Printed: information sheet and consent form (§6, §7), prompt cards, trust-rating card, SUS (VI or EN; the VI wording
  is the owner's translation, checked by a second bilingual reader under OQ-111), observer sheet.
- No audio, video or screen recording **[Pending OQ-004]**.

## 4. Data collected and analysis

| Data item | How | Personal? |
|---|---|---|
| Code, language, request time, first-proposal time, Save outcome, research used | Study log (FR-077) | Pseudonymous; no request text, no account ID |
| Both itineraries as text (Gonarra export, chatbot copy) | Saved trip / pasted text | Pseudonymous |
| Trust rating per itinerary; trust label noticed; task notes, assists | Rating card, observer sheet | Pseudonymous |
| SUS answers | Paper questionnaire | Pseudonymous |
| Age band, trips in the last 12 months, usual planning tools | Pre-task questions | Pseudonymous, banded |
| Name and signature | Consent form only | Personal — stored separately |

- MET-014: `evals/score_itinerary.py` scores both itineraries against `facts_danang.yaml` and the calendar module; a
  chatbot place that cannot be matched to a real place is counted as non-existent after a manual check, recorded per case.
- MET-001 = participants who saved a valid Gonarra itinerary ÷ participants; MET-002 = median of (first proposal
  displayed − first request), observer timing where the log is missing; MET-003 = mean SUS with standard scoring.
- Report per arm and per language; deviations listed per participant; issues that reveal defects become `DEF-xxx`.
  Results go into the test summary report by 2027-01-31.

## 5. Consent, privacy and data handling

| Topic | Rule |
|---|---|
| Consent | Written informed consent before any data is collected; participants may stop at any time without giving a reason |
| AI notice | What participants type into Gonarra goes to Google (Gemini), Groq and Tavily under free-tier terms that may allow the providers to use it; account identifiers, contact details and precise location are never sent (BR-046). The baseline arm uses the chatbot provider's own service under the owner's account. Participants should not type personal information. The same notice appears in the app (FR-074) |
| Pseudonymity | All study data uses the code `Pnn`; the only link to a name is the consent form |
| Study accounts | Pre-created, no personal e-mail or phone; deleted after the study through account deletion; pseudonymous logs kept |
| Storage | Consent forms on paper in a locked place (or encrypted scans), separate from study data; study data in an encrypted folder, never committed to git; only aggregated results enter the report |
| Retention | Study data and consent forms kept until **2027-06-30**, then destroyed; deletion checked on 2027-07-01 |
| Withdrawal | During the session or later by e-mail with the code, until 2027-06-30; figures already in a submitted report cannot be recalled **[Pending OQ-004]** |
| Cross-border | Providers process content outside Vietnam; obligations open in OQ-008 and disclosed in the consent form |
| Risks | Minimal: about 50 minutes of time; possible frustration with tasks; no sensitive data requested |
| Ethics approval | **[Pending OQ-004]** |

## 6. Consent form — English template **[Pending OQ-004]**

> **Participant information and consent — Gonarra comparative study**
>
> **Study:** Evaluation of Gonarra, a bilingual travel-planning app for Đà Nẵng, for the final-year project of Lê Ngọc
> Tấn Hiền, supervised by [mentor name and title — OQ-001], [university name]. Contact: [owner's study e-mail].
>
> **What you will do:** In one session of about 50 minutes you will plan two short Đà Nẵng trips: one with the Gonarra
> app on a phone we provide, and one with a general AI chatbot (ChatGPT or Gemini) on a laptop we provide. After each
> plan you rate how much you trust it. At the end you fill in a 10-question usability questionnaire about Gonarra.
>
> **What we collect:** a participant code (not your name), your chosen language, the times at which you requested and
> received a trip proposal, whether you saved the trip, the two itineraries, your trust ratings, the facilitator's
> notes, your questionnaire answers and a few background questions (age band, travel habits). The accounts you use
> are study accounts, not your own. Nothing is audio- or video-recorded.
>
> **AI services:** What you type into Gonarra is sent to AI and search services from Google (Gemini), Groq and Tavily,
> under free-tier terms that may allow them to use this content to improve their services, and it may be processed
> outside Vietnam. What you type into the chatbot is sent to that chatbot's provider. Your name, contact details and
> precise location are never sent by Gonarra. Please do not type personal information.
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
> - [ ] I understand that what I type is sent to external AI services as described above.
> - [ ] I agree that my pseudonymous data is used in the final-year project report.
> - [ ] I am 18 years old or over.
>
> Name: ______________________ Signature: ______________________ Date: ____ / ____ / 2027
>
> Participant code (filled in by the facilitator): P____
>
> Facilitator: Lê Ngọc Tấn Hiền — Signature: ______________________

## 7. Consent form — Vietnamese template (Phiếu đồng ý tham gia) **[Pending OQ-004]**

> **Thông tin cho người tham gia và phiếu đồng ý — Nghiên cứu so sánh ứng dụng Gonarra**
>
> **Nghiên cứu:** Đánh giá Gonarra, ứng dụng lập kế hoạch du lịch song ngữ cho Đà Nẵng, thuộc đồ án tốt nghiệp của Lê
> Ngọc Tấn Hiền, do [họ tên và học hàm của giảng viên hướng dẫn — OQ-001] hướng dẫn, [tên trường]. Liên hệ: [e-mail
> nghiên cứu của sinh viên].
>
> **Bạn sẽ làm gì:** Trong một buổi khoảng 50 phút, bạn lập kế hoạch cho hai chuyến đi ngắn ở Đà Nẵng: một chuyến bằng
> ứng dụng Gonarra trên điện thoại do chúng tôi cung cấp, và một chuyến bằng chatbot AI thông dụng (ChatGPT hoặc
> Gemini) trên máy tính xách tay do chúng tôi cung cấp. Sau mỗi kế hoạch, bạn cho biết mức độ tin tưởng của mình. Cuối
> buổi, bạn trả lời bảng hỏi 10 câu về mức độ dễ sử dụng của Gonarra.
>
> **Dữ liệu được thu thập:** mã người tham gia (không phải tên của bạn), ngôn ngữ bạn chọn, thời điểm bạn gửi yêu cầu
> và nhận đề xuất lịch trình, việc bạn có lưu chuyến đi hay không, hai lịch trình, điểm tin tưởng của bạn, ghi chú của
> người điều phối, câu trả lời bảng hỏi và vài câu hỏi chung (nhóm tuổi, thói quen du lịch). Các tài khoản dùng trong
> buổi thử là tài khoản nghiên cứu, không phải tài khoản của bạn. Buổi thử không ghi âm, không quay video.
>
> **Dịch vụ AI:** Nội dung bạn nhập vào Gonarra được gửi tới các dịch vụ AI và tìm kiếm của Google (Gemini), Groq và
> Tavily theo điều khoản gói miễn phí; các điều khoản này có thể cho phép họ dùng nội dung đó để cải thiện dịch vụ, và
> nội dung có thể được xử lý ở ngoài Việt Nam. Nội dung bạn nhập vào chatbot được gửi tới nhà cung cấp chatbot đó.
> Gonarra không bao giờ gửi họ tên, thông tin liên lạc hay vị trí chính xác của bạn. Vui lòng không nhập thông tin cá
> nhân.
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
> - [ ] Tôi hiểu rằng nội dung tôi nhập được gửi tới các dịch vụ AI bên ngoài như mô tả ở trên.
> - [ ] Tôi đồng ý cho phép dùng dữ liệu đã ẩn danh của tôi trong báo cáo đồ án tốt nghiệp.
> - [ ] Tôi từ đủ 18 tuổi trở lên.
>
> Họ tên: ______________________ Chữ ký: ______________________ Ngày: ____ / ____ / 2027
>
> Mã người tham gia (người điều phối ghi): P____
>
> Người điều phối: Lê Ngọc Tấn Hiền — Chữ ký: ______________________

## 8. Session script

The facilitator reads the script in the participant's chosen language. Text in brackets is an instruction to the
facilitator, not read aloud. "Arm 1" and "Arm 2" follow the participant's order from §2.

| Step | Time | Activity |
|---|---|---|
| 1–2 | 7 min | Welcome, information sheet, consent, code |
| 3 | 3 min | Background questions |
| 4–5 | 2 × 15 min | Arm 1 and arm 2, each followed by a trust rating |
| 6 | 2 min | Trust-label question |
| 7 | 4 min | SUS |
| 8 | 4 min | Debrief |

### 8.1 English

1. **Welcome.** "Thank you for coming. I'm testing two tools, not you — there are no wrong answers. The session takes
   about 50 minutes and you can stop at any time."
2. **Consent.** [Give the information sheet and consent form (§6). Answer questions. Collect the signed form. If not
   signed, thank the person and end.] [Assign the next code `Pnn` and its order; sign in the matching study account.]
3. **Background.** "Three quick questions: which age band are you in — 18–24, 25–34, 35–44, 45 or over? How many trips
   within Vietnam did you take in the last 12 months? Which apps do you usually use to plan trips?"
4. **Arm 1.** [Hand the prompt card for arm 1.] *Gonarra:* "Please use this app to plan the trip on the card. Fix
   anything that doesn't fit, and save the trip when you're happy." *Chatbot:* "Please use this chatbot to plan the
   trip on the card. Paste the text, ask follow-up questions if you like, and tell me when you have the plan you would
   use." [Stop at 15:00. Note the first request and first proposal times if the log fails; note assists after 2
   minutes stuck. For the chatbot, copy the final itinerary as text and take a screenshot.] [Hand the rating card.]
   "How much would you trust this plan if you followed it on the day, from 1 (not at all) to 5 (completely)?"
5. **Arm 2.** [Repeat step 4 with the other tool and the other prompt card.]
6. **Trust labels.** [After both arms.] "In Gonarra, did you notice any labels about where a place's information came
   from? What did you understand them to mean?" [Record yes/no and the answer.]
7. **SUS.** [Hand the English SUS form.] "Please answer these 10 statements about the Gonarra app."
8. **Debrief.** "What did you like most in each tool? What was most confusing? Anything else?" "Thank you. Your
   participant code is Pnn. If you want to withdraw your data before 30 June 2027, e-mail me with this code."
9. [After the participant leaves: complete the observer sheet; check the study-log entry for the code; store both
   itineraries under the code; sign the study accounts out.]

### 8.2 Tiếng Việt

1. **Chào mừng.** "Cảm ơn bạn đã đến. Mình đang thử nghiệm hai công cụ, không phải kiểm tra bạn — không có câu trả lời
   nào là sai. Buổi thử kéo dài khoảng 50 phút và bạn có thể dừng bất cứ lúc nào."
2. **Đồng ý tham gia.** [Đưa phiếu thông tin và phiếu đồng ý (§7). Trả lời câu hỏi. Nhận phiếu đã ký. Nếu không ký,
   cảm ơn và kết thúc.] [Gán mã tiếp theo `Pnn` và thứ tự tương ứng; đăng nhập tài khoản nghiên cứu.]
3. **Thông tin chung.** "Mình hỏi nhanh ba câu: bạn thuộc nhóm tuổi nào — 18–24, 25–34, 35–44 hay từ 45 trở lên? Trong
   12 tháng qua bạn đi du lịch trong nước bao nhiêu chuyến? Bạn thường dùng ứng dụng nào để lên kế hoạch du lịch?"
4. **Phần 1.** [Đưa thẻ đề bài của phần 1.] *Gonarra:* "Bạn hãy dùng ứng dụng này để lên kế hoạch cho chuyến đi ghi
   trên thẻ. Chỗ nào không hợp lý thì sửa lại, và lưu chuyến đi khi bạn thấy ổn." *Chatbot:* "Bạn hãy dùng chatbot này
   để lên kế hoạch cho chuyến đi ghi trên thẻ. Dán nội dung vào, hỏi thêm nếu muốn, và báo mình khi bạn có kế hoạch mà
   bạn sẽ dùng." [Dừng ở 15:00. Ghi thời điểm gửi yêu cầu đầu tiên và thấy đề xuất đầu tiên nếu nhật ký lỗi; ghi lại
   lần hỗ trợ khi bị kẹt quá 2 phút. Với chatbot, sao chép lịch trình cuối cùng dưới dạng văn bản và chụp màn hình.]
   [Đưa thẻ chấm điểm.] "Nếu đi theo kế hoạch này vào ngày đó, bạn tin tưởng nó đến mức nào, từ 1 (hoàn toàn không) đến
   5 (hoàn toàn tin)?"
5. **Phần 2.** [Lặp lại bước 4 với công cụ còn lại và thẻ đề bài còn lại.]
6. **Nhãn tin cậy.** [Sau cả hai phần.] "Trong Gonarra, bạn có để ý các nhãn cho biết thông tin về địa điểm lấy từ đâu
   không? Bạn hiểu các nhãn đó nghĩa là gì?" [Ghi có/không và câu trả lời.]
7. **SUS.** [Đưa bảng hỏi SUS tiếng Việt.] "Bạn hãy trả lời 10 nhận định này về ứng dụng Gonarra."
8. **Kết thúc.** "Ở mỗi công cụ, bạn thích điều gì nhất? Điều gì khó hiểu nhất? Bạn còn góp ý gì không?" "Cảm ơn bạn.
   Mã người tham gia của bạn là Pnn. Nếu muốn rút dữ liệu trước ngày 30/06/2027, bạn gửi e-mail cho mình kèm mã này."
9. [Sau khi người tham gia rời đi: hoàn thành phiếu quan sát; kiểm tra bản ghi nhật ký nghiên cứu theo mã; lưu hai lịch
   trình theo mã; đăng xuất các tài khoản nghiên cứu.]

## 9. Pilot, dependencies and approval

One pilot session with a person who is not counted (2027-01-16 or 2027-01-17) checks timing, prompt wording in both
languages, the study log, the scoring script on both arms and the forms. Changes after the pilot are recorded here
before the first counted session.

| ID | Item | Needed by |
|---|---|---|
| OQ-004 | Ethics approval and consent template — **blocks the study** | 2026-11-11 |
| OQ-008 | Cross-border data obligations — disclosed in consent | 2026-11-30 |
| OQ-111 | Second reader for the VI SUS wording and the MET-007 sample | 2026-12-08 |
| OQ-113 | Recruitment channel and compensation | 2026-12-15 |
| OQ-128 | `WEB_UNVERIFIED` stops in sessions; acknowledgement before Save | 2027-01-06 |
| OQ-130 | Baseline protocol: accounts, model versions, prompt parity | 2027-01-06 |
| OQ-131 | Mentor confirms the study claim without human catalog review (DEC-022) | 2026-11-11 |

| Role | Name | Decision | Date |
|---|---|---|---|
| Study lead | Lê Ngọc Tấn Hiền | [Pending] | — |
| Mentor | FYP mentor | [Pending] | — |
| Ethics body (if required by OQ-004) | [Pending OQ-004] | [Pending] | — |
