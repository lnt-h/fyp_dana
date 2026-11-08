import type { ClarificationRequired, IsoDate, LocalTime, Pace, Place, TravelMode, Uuid } from '../../../lib/api/types';

export type InputMode = 'form' | 'describe';

/** SCR-022 input kept in memory for the session (back from SCR-022/SCR-023 keeps it). Never persisted. */
export type PlannerDraft = {
  mode: InputMode;
  cityId: Uuid | null;
  startDate: IsoDate | null;
  dayCount: 1 | 2 | 3 | null;
  dayStart: LocalTime;
  dayEnd: LocalTime;
  pace: Pace;
  interests: string[];
  modes: TravelMode[];
  mustSee: Pick<Place, 'id' | 'name'>[];
  requestText: string;
  /** Optional trip name (`TripCreate.title`), set on the wizard's review step. */
  title?: string;
  /** True once prefill from saved preferences (API-004) was applied. */
  prefilled: boolean;
};

export type PlannerView =
  | { kind: 'input' }
  | { kind: 'clarify'; clarification: ClarificationRequired }
  | { kind: 'unsupported' };

let draft: PlannerDraft | null = null;
let pendingView: PlannerView | null = null;
let aiNoticeAcknowledged = false;

export const readDraft = () => draft;
export const writeDraft = (next: PlannerDraft) => { draft = next; };

/** SCR-023 hands a clarification or a refusal back to SCR-022 through this one-shot slot. */
export function setPendingView(view: PlannerView) { pendingView = view; }
export function takePendingView(): PlannerView | null {
  const view = pendingView;
  pendingView = null;
  return view;
}

/** First-use AI notice (FR-073); in memory until API-005 is wired. */
export const isAiNoticeAcknowledged = () => aiNoticeAcknowledged;
export const acknowledgeAiNotice = () => { aiNoticeAcknowledged = true; };
