import i18n from '../../i18n';

export function authErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'errors' in error && Array.isArray(error.errors)) {
    const detail = error.errors[0];
    if (typeof detail?.longMessage === 'string') return detail.longMessage;
    if (typeof detail?.message === 'string') return detail.message;
  }
  return i18n.t('auth.errors.generic');
}
