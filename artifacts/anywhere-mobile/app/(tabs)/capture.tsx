import { Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useState } from 'react';
import {
  ActivityIndicator,
  Keyboard,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { KeyboardAwareScrollViewCompat } from '@/components/KeyboardAwareScrollViewCompat';
import { Atmosphere, GlassPanel } from '@/components/Atmosphere';
import { useProjectStack, type IntentOutcome } from '@/context/ProjectContext';
import { useColors } from '@/hooks/useColors';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const suggestions = [
  'Help me decide what to focus on next',
  'Capture a decision and its reason',
  'Plan the next step for this project',
];

export default function CaptureScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { online, liveAIReady, checkingConnection, busy, submitIntent } = useProjectStack();
  const [text, setText] = useState('');
  const [outcome, setOutcome] = useState<IntentOutcome | null>(null);

  const send = async () => {
    if (!text.trim() || busy) return;
    Keyboard.dismiss();
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const result = await submitIntent(text);
    setOutcome(result);
    setText('');
  };

  const statusText = checkingConnection
    ? 'Checking your connection'
    : liveAIReady
      ? 'Live AI is ready'
      : online
        ? 'Local capture · live AI unavailable'
        : 'Offline · intents stay on this device';

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <Atmosphere />
      <KeyboardAwareScrollViewCompat
        style={styles.scroll}
        contentContainerStyle={{
          paddingTop: (Platform.OS === 'web' ? 67 : insets.top) + 20,
          paddingHorizontal: 22,
          paddingBottom: Math.max(insets.bottom, Platform.OS === 'web' ? 34 : 18) + 112,
        }}
        keyboardShouldPersistTaps="handled"
        bottomOffset={24}
      >
        <View style={styles.eyebrow}>
          <Feather name="aperture" size={14} color={colors.primary} />
          <Text style={[styles.eyebrowText, { color: colors.mutedForeground }]}>INTENT INBOX</Text>
        </View>
        <Text style={[styles.title, { color: colors.foreground }]}>What’s on your mind?</Text>
        <Text style={[styles.subtitle, { color: colors.mutedForeground }]}>
          Write naturally. Your context moves with you.
        </Text>

        <GlassPanel style={styles.composerPanel} strong>
          <TextInput
            testID="intent-input"
            accessibilityLabel="Write an intent"
            value={text}
            onChangeText={(value) => {
              setText(value);
              if (outcome) setOutcome(null);
            }}
            placeholder="A decision, an idea, a next step…"
            placeholderTextColor={colors.mutedForeground}
            multiline
            textAlignVertical="top"
            maxLength={2000}
            style={[styles.input, { color: colors.foreground }]}
            returnKeyType="default"
          />
          <View style={styles.composerFooter}>
            <Text style={[styles.characterCount, { color: colors.mutedForeground }]}>
              {text.length}/2000
            </Text>
            <Pressable
              testID="send-intent"
              accessibilityRole="button"
              accessibilityLabel="Send intent"
              onPress={() => void send()}
              disabled={!text.trim() || busy}
              style={({ pressed }) => [
                styles.sendButton,
                { backgroundColor: colors.primary, opacity: !text.trim() || busy ? 0.46 : pressed ? 0.82 : 1 },
              ]}
            >
              {busy ? (
                <ActivityIndicator size="small" color={colors.primaryForeground} />
              ) : (
                <>
                  <Text style={[styles.sendLabel, { color: colors.primaryForeground }]}>
                    {liveAIReady ? 'Process' : 'Save intent'}
                  </Text>
                  <Feather name="arrow-up-right" size={17} color={colors.primaryForeground} />
                </>
              )}
            </Pressable>
          </View>
        </GlassPanel>

        <View style={[styles.statusRow, { borderColor: colors.border }]}>
          <View
            style={[
              styles.statusDot,
              { backgroundColor: liveAIReady ? colors.success : colors.warning },
            ]}
          />
          <Text style={[styles.statusText, { color: colors.mutedForeground }]}>{statusText}</Text>
        </View>

        {outcome ? (
          <GlassPanel
            style={[
              styles.outcomePanel,
              { borderColor: outcome.status === 'error' ? colors.destructive : colors.glassBorder },
            ]}
          >
            <View style={styles.outcomeHeading}>
              <Feather
                name={
                  outcome.status === 'processed'
                    ? 'check-circle'
                    : outcome.status === 'queued'
                      ? 'inbox'
                      : 'alert-circle'
                }
                size={17}
                color={outcome.status === 'error' ? colors.destructive : colors.primary}
              />
              <Text style={[styles.outcomeLabel, { color: colors.foreground }]}>
                {outcome.status === 'processed'
                  ? 'Project Brain updated'
                  : outcome.status === 'queued'
                    ? 'Saved for later'
                    : 'Not sent'}
              </Text>
            </View>
            <Text style={[styles.outcomeText, { color: colors.mutedForeground }]}>
              {outcome.message}
            </Text>
          </GlassPanel>
        ) : null}

        <Text style={[styles.sectionTitle, { color: colors.mutedForeground, marginTop: 27 }]}>
          START WITH A THOUGHT
        </Text>
        {suggestions.map((suggestion) => (
          <Pressable
            key={suggestion}
            accessibilityRole="button"
            onPress={() => {
              setText(suggestion);
              setOutcome(null);
            }}
            style={({ pressed }) => [styles.suggestion, { borderBottomColor: colors.border, opacity: pressed ? 0.65 : 1 }]}
          >
            <Text style={[styles.suggestionText, { color: colors.foreground }]}>{suggestion}</Text>
            <Feather name="arrow-up-left" size={15} color={colors.mutedForeground} />
          </Pressable>
        ))}
      </KeyboardAwareScrollViewCompat>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  scroll: { flex: 1 },
  eyebrow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  eyebrowText: { fontSize: 11, letterSpacing: 1.7, fontFamily: 'Inter_600SemiBold' },
  title: { fontSize: 32, lineHeight: 38, letterSpacing: -1.1, fontFamily: 'Inter_600SemiBold' },
  subtitle: { fontSize: 15, lineHeight: 22, marginTop: 8, marginBottom: 24, fontFamily: 'Inter_400Regular' },
  composerPanel: { minHeight: 215 },
  input: { minHeight: 132, fontSize: 17, lineHeight: 25, fontFamily: 'Inter_400Regular' },
  composerFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 },
  characterCount: { fontSize: 12, fontFamily: 'Inter_400Regular' },
  sendButton: { minHeight: 44, borderRadius: 22, paddingHorizontal: 17, flexDirection: 'row', alignItems: 'center', gap: 8 },
  sendLabel: { fontSize: 14, fontFamily: 'Inter_600SemiBold' },
  statusRow: { flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 15, borderBottomWidth: StyleSheet.hairlineWidth },
  statusDot: { width: 7, height: 7, borderRadius: 4 },
  statusText: { fontSize: 12, fontFamily: 'Inter_500Medium' },
  outcomePanel: { marginTop: 17 },
  outcomeHeading: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 8 },
  outcomeLabel: { fontSize: 14, fontFamily: 'Inter_600SemiBold' },
  outcomeText: { fontSize: 14, lineHeight: 21, fontFamily: 'Inter_400Regular' },
  sectionTitle: { fontSize: 10, letterSpacing: 1.4, fontFamily: 'Inter_600SemiBold', marginTop: 26, marginBottom: 12 },
  suggestion: { minHeight: 48, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderBottomWidth: StyleSheet.hairlineWidth, gap: 12 },
  suggestionText: { flex: 1, fontSize: 14, fontFamily: 'Inter_400Regular' },
});
