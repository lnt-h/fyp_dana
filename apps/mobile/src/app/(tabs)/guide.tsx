import { useTranslation } from 'react-i18next';

import { TabPlaceholder } from '../../features/tabs/TabPlaceholder';

export default function GuideScreen() {
  const { t } = useTranslation();
  return <TabPlaceholder title={t('tabs.placeholder.guide.title')} subtitle={t('tabs.placeholder.guide.subtitle')} />;
}
