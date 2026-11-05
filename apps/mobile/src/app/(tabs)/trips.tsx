import { useTranslation } from 'react-i18next';

import { TabPlaceholder } from '../../features/tabs/TabPlaceholder';

export default function TripsScreen() {
  const { t } = useTranslation();
  return <TabPlaceholder title={t('tabs.placeholder.trips.title')} subtitle={t('tabs.placeholder.trips.subtitle')} />;
}
