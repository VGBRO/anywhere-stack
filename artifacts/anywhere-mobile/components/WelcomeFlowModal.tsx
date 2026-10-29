import { Feather } from '@expo/vector-icons';
import { useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Atmosphere, GlassPanel, OrbitalMark } from '@/components/Atmosphere';
import { useColors } from '@/hooks/useColors';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export function WelcomeFlowModal({
  visible,
  onComplete,
}: {
  visible: boolean;
  onComplete: () => void;
}) {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const [step, setStep] = useState<'welcome' | 'sign-in'>('welcome');
  const [method, setMethod] = useState<'face' | 'voice' | null>(null);

  const continueDemo = (selectedMethod: 'face' | 'voice') => {
    setStep('sign-in');
    setMethod(selectedMethod);
    setTimeout(onComplete, 900);
  };

  return (
    <Modal
      visible={visible}
      animationType="none"
      transparent={false}
      statusBarTranslucent
      onRequestClose={() => {
        if (step === 'sign-in') setStep('welcome');
      }}
    >
      <View style={[styles.root, { backgroundColor: colors.skyTop }]}>
        <Atmosphere />
        <View
          style={[
            styles.content,
            {
              paddingTop: (Platform.OS === 'web' ? 32 : insets.top) + 16,
              paddingBottom: Math.max(insets.bottom, Platform.OS === 'web' ? 25 : 20),
            },
          ]}
        >
          {step === 'welcome' ? (
            <>
              <Text style={styles.tapLabel}>TAP TO BEGIN</Text>
              <View style={styles.welcomeCard}>
                <GlassPanel style={styles.glassCard} strong>
                  <View style={styles.brandRow}>
                    <OrbitalMark size={44} color={colors.foreground} />
                    <View>
                      <Text style={[styles.brandName, { color: colors.foreground }]}>Anywhere</Text>
                      <Text style={[styles.brandStack, { color: colors.mutedForeground }]}>STACK</Text>
                    </View>
                  </View>
                  <Text style={[styles.tagline, { color: colors.secondaryForeground }]}>
                    Your life is the prompt. Everything else is output.
                  </Text>
                  <Pressable
                    testID="welcome-get-started"
                    accessibilityRole="button"
                    onPress={() => setStep('sign-in')}
                    style={({ pressed }) => [
                      styles.primaryButton,
                      { backgroundColor: colors.primary, opacity: pressed ? 0.84 : 1 },
                    ]}
                  >
                    <Text style={[styles.primaryLabel, { color: colors.primaryForeground }]}>Get started</Text>
                    <Feather name="arrow-right" size={16} color={colors.primaryForeground} />
                  </Pressable>
                  <View style={styles.authShortcuts}>
                    <Pressable
                      testID="welcome-face-login"
                      accessibilityRole="button"
                      onPress={() => continueDemo('face')}
                      style={({ pressed }) => [
                        styles.shortcutButton,
                        { backgroundColor: colors.card, borderColor: colors.border, opacity: pressed ? 0.78 : 1 },
                      ]}
                    >
                      <Feather name="eye" size={16} color={colors.primary} />
                      <Text style={[styles.shortcutLabel, { color: colors.foreground }]}>
                        Login with Face Recognition
                      </Text>
                    </Pressable>
                    <Pressable
                      testID="welcome-voice-login"
                      accessibilityRole="button"
                      onPress={() => continueDemo('voice')}
                      style={({ pressed }) => [
                        styles.shortcutButton,
                        { backgroundColor: colors.card, borderColor: colors.border, opacity: pressed ? 0.78 : 1 },
                      ]}
                    >
                      <Feather name="mic" size={16} color={colors.primary} />
                      <Text style={[styles.shortcutLabel, { color: colors.foreground }]}>
                        Login with Voice Recognition
                      </Text>
                    </Pressable>
                  </View>
                  <Text style={[styles.shortcutDisclaimer, { color: colors.mutedForeground }]}>
                    Preview only. No identity check is performed.
                  </Text>
                </GlassPanel>
              </View>
            </>
          ) : (
            <View style={styles.signInCard}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Back to welcome"
                onPress={() => {
                  setMethod(null);
                  setStep('welcome');
                }}
                style={styles.backButton}
              >
                <Feather name="arrow-left" size={18} color={colors.foreground} />
              </Pressable>
              <GlassPanel style={styles.glassCard} strong>
                <Text style={[styles.signInTitle, { color: colors.foreground }]}>Sign in</Text>
                <Text style={[styles.signInSubtitle, { color: colors.secondaryForeground }]}>
                  Your intelligence is waiting.
                </Text>
                <View style={styles.biometricStage}>
                  <View style={[styles.biometricCore, { backgroundColor: colors.glassStrong }]}>
                    <View style={[styles.biometricDot, { backgroundColor: colors.primary }]} />
                  </View>
                  {method ? (
                    <View style={[styles.scanRing, { borderColor: colors.primary }]} />
                  ) : null}
                </View>
                <Text style={[styles.authStatus, { color: method ? colors.primary : colors.mutedForeground }]}>
                  {method
                    ? 'Preview confirmed — no identity check was performed.'
                    : 'Choose a sign-in preview to continue.'}
                </Text>
                <Pressable
                  testID="demo-face-sign-in"
                  accessibilityRole="button"
                  disabled={method !== null}
                  onPress={() => continueDemo('face')}
                  style={({ pressed }) => [
                    styles.authButton,
                    { backgroundColor: colors.card, borderColor: colors.border, opacity: pressed ? 0.78 : 1 },
                  ]}
                >
                  {method === 'face' ? (
                    <ActivityIndicator color={colors.primary} />
                  ) : (
                    <Feather name="eye" size={19} color={colors.primary} />
                  )}
                  <Text style={[styles.authButtonLabel, { color: colors.foreground }]}>
                    Login with Face Recognition
                  </Text>
                  <Text style={[styles.previewBadge, { backgroundColor: colors.muted, color: colors.mutedForeground }]}>
                    Preview
                  </Text>
                </Pressable>
                <Pressable
                  testID="demo-voice-sign-in"
                  accessibilityRole="button"
                  disabled={method !== null}
                  onPress={() => continueDemo('voice')}
                  style={({ pressed }) => [
                    styles.authButton,
                    { backgroundColor: colors.card, borderColor: colors.border, opacity: pressed ? 0.78 : 1 },
                  ]}
                >
                  {method === 'voice' ? (
                    <ActivityIndicator color={colors.primary} />
                  ) : (
                    <Feather name="mic" size={19} color={colors.primary} />
                  )}
                  <Text style={[styles.authButtonLabel, { color: colors.foreground }]}>
                    Login with Voice Recognition
                  </Text>
                  <Text style={[styles.previewBadge, { backgroundColor: colors.muted, color: colors.mutedForeground }]}>
                    Preview
                  </Text>
                </Pressable>
                <Text style={[styles.authFooter, { color: colors.mutedForeground }]}>
                  Demo access only. This does not verify identity or secure an account.
                </Text>
              </GlassPanel>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { flex: 1, justifyContent: 'space-between' },
  tapLabel: { marginTop: 8, textAlign: 'center', color: 'rgba(255,255,255,0.7)', fontSize: 10, letterSpacing: 2, fontFamily: 'Inter_500Medium' },
  welcomeCard: { paddingHorizontal: 20 },
  glassCard: { padding: 0, borderRadius: 24 },
  brandRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12 },
  brandName: { fontSize: 31, lineHeight: 35, fontFamily: 'Inter_600SemiBold', letterSpacing: -0.4 },
  brandStack: { fontSize: 15, lineHeight: 20, letterSpacing: 5, fontFamily: 'Inter_400Regular' },
  tagline: { marginTop: 19, marginBottom: 22, textAlign: 'center', fontSize: 16, lineHeight: 23, fontFamily: 'Inter_400Regular' },
  primaryButton: { minHeight: 48, borderRadius: 25, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  primaryLabel: { fontSize: 15, fontFamily: 'Inter_600SemiBold' },
  authShortcuts: { gap: 8, marginTop: 11 },
  shortcutButton: { minHeight: 42, borderWidth: 1, borderRadius: 15, paddingHorizontal: 13, flexDirection: 'row', alignItems: 'center', gap: 10 },
  shortcutLabel: { flex: 1, fontSize: 12, fontFamily: 'Inter_500Medium' },
  shortcutDisclaimer: { marginTop: 8, textAlign: 'center', fontSize: 10, lineHeight: 15, fontFamily: 'Inter_400Regular' },
  signInCard: { paddingHorizontal: 20, paddingBottom: 10 },
  backButton: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', marginBottom: 9 },
  signInTitle: { fontSize: 27, letterSpacing: -0.3, fontFamily: 'Inter_600SemiBold' },
  signInSubtitle: { marginTop: 4, fontSize: 15, fontFamily: 'Inter_400Regular' },
  biometricStage: { height: 96, alignItems: 'center', justifyContent: 'center' },
  biometricCore: { width: 58, height: 58, borderRadius: 29, alignItems: 'center', justifyContent: 'center' },
  biometricDot: { width: 7, height: 7, borderRadius: 4 },
  scanRing: { position: 'absolute', width: 76, height: 76, borderWidth: 1, borderRadius: 38, opacity: 0.5 },
  authStatus: { minHeight: 36, textAlign: 'center', fontSize: 12, lineHeight: 18, marginBottom: 12, fontFamily: 'Inter_400Regular' },
  authButton: { minHeight: 53, borderWidth: 1, borderRadius: 18, paddingHorizontal: 15, flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  authButtonLabel: { flex: 1, fontSize: 14, fontFamily: 'Inter_500Medium' },
  previewBadge: { overflow: 'hidden', borderRadius: 10, paddingVertical: 4, paddingHorizontal: 9, fontSize: 10, fontFamily: 'Inter_400Regular' },
  authFooter: { textAlign: 'center', fontSize: 11, lineHeight: 17, marginTop: 8, fontFamily: 'Inter_400Regular' },
});
