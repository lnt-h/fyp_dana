import { useTranslation } from 'react-i18next';

import { TabPlaceholder } from '../../features/tabs/TabPlaceholder';
import { defaultCity } from '../../lib/api/fixtures/hoi-an';

export default function ExploreScreen() {
  const { t, i18n } = useTranslation();
  const city = i18n.resolvedLanguage === 'vi' ? defaultCity.name_vi : defaultCity.name_en;
  return <TabPlaceholder title={t('tabs.placeholder.explore.title', { city })} subtitle={t('tabs.placeholder.explore.subtitle')} />;
}
