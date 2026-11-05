import type { ReactNode } from 'react';
import { KeyboardAvoidingView, Modal, Platform, Pressable, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';

type Props = {
  visible: boolean;
  /** Called on backdrop tap, Android back or swipe; ignored while `dismissible` is false (e.g. while applying). */
  onClose: () => void;
  dismissible?: boolean;
  /** Spoken name of the dialog (S-4: sheets are modal dialogs). */
  accessibilityLabel: string;
  role?: 'dialog' | 'alertdialog';
  children: ReactNode;
  /** Fixed footer under the scrollable body (primary action). */
  footer?: ReactNode;
};

/** Bottom sheet over the proposal: radius 40, handle, modal focus trap, no slide animation under reduced motion. */
export function Sheet({ visible, onClose, dismissible = true, accessibilityLabel, role = 'dialog', children, footer }: Props) {
  const insets = useSafeAreaInsets();
  const reducedMotion = useReducedMotion();
  const close = () => { if (dismissible) onClose(); };
  return <Modal animationType={reducedMotion ? 'none' : 'slide'} onRequestClose={close} statusBarTranslucent transparent visible={visible}>
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={s.backdrop}>
      <Pressable accessibilityElementsHidden importantForAccessibility="no-hide-descendants" onPress={close} style={StyleSheet.absoluteFill} />
      <View
        accessibilityLabel={accessibilityLabel}
        role={role}
        accessibilityViewIsModal
        style={[s.sheet, { paddingBottom: Math.max(insets.bottom, spacing.sm) + spacing.xs }]}
      >
        <View style={s.handle} />
        <View style={s.body}>{children}</View>
        {footer ? <View style={s.footer}>{footer}</View> : null}
      </View>
    </KeyboardAvoidingView>
  </Modal>;
}

const s = StyleSheet.create({
  backdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(7,21,30,0.45)' },
  sheet: { maxHeight: '92%', backgroundColor: colors.white, borderTopLeftRadius: radii.sheet, borderTopRightRadius: radii.sheet, paddingTop: spacing.xs, width: '100%', maxWidth: 560, alignSelf: 'center' },
  handle: { alignSelf: 'center', width: 44, height: 5, borderRadius: 3, backgroundColor: colors.mutedDot, marginBottom: spacing.xs },
  body: { flexShrink: 1 },
  footer: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.hairline },
});
