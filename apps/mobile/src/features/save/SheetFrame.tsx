import { useEffect, useRef, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Animated, Easing, Modal, Pressable, ScrollView, StyleSheet, useWindowDimensions, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useReducedMotion } from '../../hooks/useReducedMotion';
import { colors } from '../../theme/colors';
import { radii, spacing } from '../../theme/spacing';

const DURATION = 220;

export type SheetFrameProps = {
  visible: boolean;
  /** Back button, backdrop tap. Ignored while `dismissible` is false (e.g. a Save request in flight). */
  onRequestClose: () => void;
  dismissible?: boolean;
  /** Spoken name of the dialog. */
  accessibilityLabel: string;
  children: ReactNode;
  /** Pinned under the scroll area (primary actions). */
  footer?: ReactNode;
};

/**
 * Modal bottom sheet (radius 40, handle, ink scrim) shared by SCR-029 and SCR-037. Slides in ≤ 220 ms; appears without
 * motion when reduced motion is on (S-4). Traps screen-reader focus via `accessibilityViewIsModal`.
 */
export function SheetFrame({ visible, onRequestClose, dismissible = true, accessibilityLabel, children, footer }: SheetFrameProps) {
  const { t } = useTranslation();
  const reduced = useReducedMotion();
  const insets = useSafeAreaInsets();
  const { height } = useWindowDimensions();
  const progress = useRef(new Animated.Value(0)).current;
  const [mounted, setMounted] = useState(visible);

  useEffect(() => {
    if (visible) setMounted(true);
    const animation = Animated.timing(progress, {
      duration: reduced ? 0 : DURATION,
      easing: visible ? Easing.out(Easing.cubic) : Easing.in(Easing.cubic),
      toValue: visible ? 1 : 0,
      useNativeDriver: true,
    });
    animation.start(({ finished }) => {
      if (finished && !visible) setMounted(false);
    });
    return () => animation.stop();
  }, [progress, reduced, visible]);

  const close = () => {
    if (dismissible) onRequestClose();
  };

  const translateY = progress.interpolate({ inputRange: [0, 1], outputRange: [height * 0.4, 0] });

  return (
    <Modal animationType="none" onRequestClose={close} statusBarTranslucent transparent visible={mounted}>
      <View style={styles.root}>
        <Animated.View style={[StyleSheet.absoluteFill, styles.scrim, { opacity: progress }]}>
          <Pressable
            accessibilityLabel={t('save.sheet.close')}
            accessibilityRole="button"
            disabled={!dismissible}
            onPress={close}
            style={StyleSheet.absoluteFill}
          />
        </Animated.View>
        <Animated.View
          accessibilityLabel={accessibilityLabel}
          accessibilityViewIsModal
          style={[styles.sheet, { maxHeight: height * 0.92, paddingBottom: Math.max(insets.bottom, spacing.md), transform: [{ translateY }] }]}
        >
          <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.handle} />
          <ScrollView bounces={false} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
            {children}
          </ScrollView>
          {footer ? <View style={styles.footer}>{footer}</View> : null}
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  content: { gap: spacing.md, paddingHorizontal: spacing.lg, paddingTop: spacing.xs },
  footer: { gap: spacing.xs, paddingHorizontal: spacing.lg, paddingTop: spacing.sm },
  handle: { alignSelf: 'center', backgroundColor: colors.mutedDot, borderRadius: 3, height: 5, marginBottom: spacing.sm, marginTop: spacing.sm, width: 44 },
  root: { flex: 1, justifyContent: 'flex-end' },
  scrim: { backgroundColor: 'rgba(7,21,30,0.5)' },
  sheet: { backgroundColor: colors.white, borderTopLeftRadius: radii.sheet, borderTopRightRadius: radii.sheet },
});
