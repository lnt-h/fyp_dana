import { useTranslation } from 'react-i18next';

import { SecondaryButton } from '../../components/ui';
import type { HandoffKind, Uuid } from '../../lib/api/types';
import { SheetFrame } from '../save/SheetFrame';
import { HandoffPanel } from './HandoffPanel';

export type HandoffSheetProps = {
  visible: boolean;
  tripId: Uuid;
  /** Default all kinds; pass `['STAY']`, `['ACTIVITY']` (with `stopId`) or `['TRANSPORT']` for a single-purpose sheet. */
  kinds?: HandoffKind[];
  stopId?: Uuid;
  onClose: () => void;
};

/**
 * SCR-037 Booking handoff sheet. Only for SAVED trips (the API answers 409 `trip_not_saved` otherwise): hide the entry
 * point on unsaved drafts.
 */
export function HandoffSheet({ visible, tripId, kinds, stopId, onClose }: HandoffSheetProps) {
  const { t } = useTranslation();
  return (
    <SheetFrame
      accessibilityLabel={t('save.handoff.title')}
      footer={<SecondaryButton label={t('save.handoff.close')} onPress={onClose} />}
      onRequestClose={onClose}
      visible={visible}
    >
      {visible ? <HandoffPanel kinds={kinds} stopId={stopId} tripId={tripId} /> : null}
    </SheetFrame>
  );
}
