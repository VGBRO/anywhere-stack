import AsyncStorage from '@react-native-async-storage/async-storage';
import { Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { GlassPanel, OrbitalMark } from '@/components/Atmosphere';
import { VoiceCaptureModal } from '@/components/VoiceCaptureModal';
import { WelcomeFlowModal } from '@/components/WelcomeFlowModal';
import { useProjectStack } from '@/context/ProjectContext';
import { useColors } from '@/hooks/useColors';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const WELCOME_KEY = '@anywhere-stack/welcome-complete';

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning.';
  if (hour < 17) return 'Good afternoon.';
  return 'Good evening.';
}

export function ProjectsHomeScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const {
    projects,
    queue,
    online,
    offlineMode,
    liveAIReady,
    firmMode,
    checkingConnection,
    busy,
    storageWarning,
    refreshConnection,
    toggleConnection,
    toggleFirmMode,
    submitIntent,
  } = useProjectStack();
  const [text, setText] = useState('');
  const [intentStatus, setIntentStatus] = useState('');
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [welcomeVisible, setWelcomeVisible] = useState(true);
  const greetingText = useMemo(greeting, []);

  useEffect(() => {
    let active = true;
    AsyncStorage.getItem(WELCOME_KEY)
      .then((value) => {
        if (active && value === 'complete') setWelcomeVisible(false);
      })
      .catch(() => {
        if (active) setWelcomeVisible(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const completeWelcome = () => {
    setWelcomeVisible(false);
    void AsyncStorage.setItem(WELCOME_KEY, 'complete').catch(() => undefined);
  };

  const sendIntent = async (value: string) => {
    const intent = value.trim();
    if (!intent || busy) return;
    setIntentStatus(liveAIReady ? 'Routing via Nemotron NANO…' : 'Capturing locally…');
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const outcome = await submitIntent(intent);
    setText('');
    setIntentStatus(
      outcome.status === 'processed'
        ? 'Updated by Nemotron.'
        : outcome.message,
    );
  };

  const setOffline = async () => {
    const message = await toggleConnection();
    setIntentStatus(message);
  };

  const rootBackground = firmMode ? colors.firmBackground : colors.background;
  const bottomOffset = Platform.OS === 'web' ? 83 : Math.max(insets.bottom, 12) + 53;

  return (
    <View style={[styles.root, { backgroundColor: rootBackground }]}>
      {offlineMode ? (
        <View pointerEvents="none" style={[styles.offlineRing, { borderColor: colors.offline }]} />
      ) : null}
      <ScrollView
        contentInsetAdjustmentBehavior="never"
        contentContainerStyle={{
          paddingTop: (Platform.OS === 'web' ? 64 : insets.top) + 4,
          paddingHorizontal: 24,
          paddingBottom: bottomOffset + 112,
        }}
        keyboardShouldPersistTaps="handled"
      >
        <View style={[styles.homeNav, { backgroundColor: rootBackground, borderBottomColor: colors.muted }]}>
          <View style={styles.brand}>
            <OrbitalMark size={20} color={colors.foreground} />
            <Text style={[styles.brandLabel, { color: colors.mutedForeground }]}>ANYWHERE</Text>
          </View>
          <View style={styles.controls}>
            {firmMode ? (
              <View style={[styles.firmBadge, { backgroundColor: 'rgba(180,140,80,0.12)', borderColor: 'rgba(180,140,80,0.3)' }]}>
                <Text style={[styles.firmBadgeText, { color: colors.firmGold }]}>FIRM OS</Text>
              </View>
            ) : null}
            <Pressable
              testID="online-toggle"
              accessibilityRole="button"
              accessibilityLabel={offlineMode ? 'Turn online mode on' : 'Turn offline mode on'}
              onPress={() => void setOffline()}
              style={({ pressed }) => [
                styles.onlinePill,
                {
                  backgroundColor: offlineMode ? 'rgba(255,59,48,0.14)' : 'rgba(210,210,215,0.64)',
                  opacity: pressed ? 0.8 : 1,
                },
              ]}
            >
              {checkingConnection ? (
                <ActivityIndicator size="small" color={colors.primary} />
              ) : (
                <View style={[styles.onlineDot, { backgroundColor: offlineMode ? colors.offline : colors.success }]} />
              )}
              <Text style={[styles.onlineLabel, { color: colors.foreground }]}>
                {offlineMode ? 'Offline' : 'Online'}
              </Text>
            </Pressable>
            <Pressable
              testID="firm-mode-toggle"
              accessibilityRole="button"
              accessibilityLabel={firmMode ? 'Switch to personal mode' : 'Switch to Firm OS mode'}
              accessibilityState={{ selected: firmMode }}
              onPress={toggleFirmMode}
              style={({ pressed }) => [
                styles.firmButton,
                { backgroundColor: firmMode ? colors.firmGold : '#272729', opacity: pressed ? 0.78 : 1 },
              ]}
            >
              <Text style={styles.firmButtonLabel}>{firmMode ? 'Personal' : 'Firm OS'}</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.greetingBlock}>
          <Text style={[styles.greeting, { color: colors.foreground }]}>{greetingText}</Text>
          <Text style={[styles.greetingSub, { color: colors.mutedForeground }]}>Your world is moving.</Text>
        </View>

        {storageWarning ? (
          <View style={[styles.storageWarning, { backgroundColor: colors.accent }]}>
            <Feather name="alert-circle" size={15} color={colors.warning} />
            <Text style={[styles.storageWarningText, { color: colors.foreground }]}>{storageWarning}</Text>
          </View>
        ) : null}

        <View style={styles.projectsHeader}>
          <Text style={[styles.sectionLabel, { color: colors.mutedForeground }]}>ACTIVE PROJECTS</Text>
          {queue.length ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${queue.length} intents waiting in inbox`}
              onPress={() => router.push('/(tabs)/inbox')}
              style={[styles.queuePill, { backgroundColor: colors.accent }]}
            >
              <Feather name="inbox" size={13} color={colors.accentForeground} />
              <Text style={[styles.queueLabel, { color: colors.accentForeground }]}>{queue.length} waiting</Text>
            </Pressable>
          ) : null}
        </View>

        {projects.map((project) => (
          <Pressable
            key={project.id}
            testID={`project-${project.id}`}
            accessibilityRole="button"
            accessibilityLabel={`Open ${project.name} Project Brain`}
            onPress={() => router.push({ pathname: '/project/[id]', params: { id: project.id } })}
            style={({ pressed }) => [styles.projectPressable, { opacity: pressed ? 0.94 : 1 }]}
          >
            <GlassPanel
              style={[
                styles.projectCard,
                {
                  backgroundColor: colors.card,
                  borderColor: colors.border,
                },
              ]}
            >
              <View style={styles.projectTop}>
                <Text style={[styles.projectName, { color: colors.foreground }]}>{project.name}</Text>
                <View
                  style={[
                    styles.scopeBadge,
                    {
                      backgroundColor: project.scope === 'work' ? 'rgba(180,140,80,0.07)' : 'rgba(0,102,204,0.06)',
                      borderColor: project.scope === 'work' ? 'rgba(180,140,80,0.25)' : 'rgba(0,102,204,0.22)',
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.scopeBadgeText,
                      { color: project.scope === 'work' ? colors.firmGold : colors.primary },
                    ]}
                  >
                    {project.scope}
                  </Text>
                </View>
              </View>
              <Text style={[styles.projectState, { color: colors.secondaryForeground }]}>{project.state}</Text>
              <View style={styles.tags}>
                {project.tags.map((tag) => (
                  <View key={tag} style={[styles.tag, { backgroundColor: colors.background, borderColor: colors.muted }]}>
                    <Text style={[styles.tagText, { color: colors.mutedForeground }]}>{tag}</Text>
                  </View>
                ))}
              </View>
              {project.updates.length > 0 ? (
                <View style={[styles.projectFlash, { borderTopColor: colors.muted }]}>
                  <Text style={[styles.projectFlashText, { color: colors.primary }]}>
                    Updated by Nemotron → {project.actions[0] || 'Brain updated'}
                  </Text>
                </View>
              ) : null}
            </GlassPanel>
          </Pressable>
        ))}
      </ScrollView>

      <View
        style={[
          styles.intentDock,
          {
            bottom: bottomOffset,
            backgroundColor: firmMode ? 'rgba(236,236,236,0.92)' : 'rgba(245,245,247,0.9)',
            borderTopColor: colors.border,
            paddingBottom: Platform.OS === 'web' ? 12 : 9,
          },
        ]}
      >
        <View style={styles.dockStatusRow}>
          <Text
            numberOfLines={1}
            accessibilityLiveRegion="polite"
            style={[styles.intentStatus, { color: offlineMode ? colors.offline : liveAIReady ? colors.mutedForeground : colors.warning }]}
          >
            {intentStatus ||
              (offlineMode
                ? `Captured locally${queue.length ? ` — ${queue.length} waiting` : ''}`
                : liveAIReady
                  ? ''
                  : 'Live AI unavailable — intents stay on this device')}
          </Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Refresh server connection"
            onPress={() => void refreshConnection()}
            hitSlop={8}
            style={styles.refreshButton}
          >
            <Feather name="refresh-cw" size={12} color={colors.mutedForeground} />
          </Pressable>
        </View>
        <View style={[styles.intentBar, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <TextInput
            testID="intent-input"
            accessibilityLabel="What's on your mind?"
            value={text}
            onChangeText={setText}
            onSubmitEditing={() => void sendIntent(text)}
            placeholder="What’s on your mind…"
            placeholderTextColor={colors.mutedForeground}
            maxLength={2000}
            returnKeyType="send"
            submitBehavior="submit"
            style={[styles.intentInput, { color: colors.foreground }]}
          />
          <Pressable
            testID="open-voice-capture"
            accessibilityRole="button"
            accessibilityLabel="Open voice capture"
            onPress={() => setVoiceOpen(true)}
            style={({ pressed }) => [styles.micButton, { backgroundColor: colors.primary, opacity: pressed ? 0.82 : 1 }]}
          >
            <Feather name="mic" size={16} color={colors.primaryForeground} />
          </Pressable>
        </View>
      </View>

      <VoiceCaptureModal
        visible={voiceOpen}
        onClose={() => setVoiceOpen(false)}
        onSubmit={async (value) => {
          setVoiceOpen(false);
          await sendIntent(value);
        }}
      />
      <WelcomeFlowModal visible={welcomeVisible} onComplete={completeWelcome} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  offlineRing: { ...StyleSheet.absoluteFill, zIndex: 5, borderWidth: 2, opacity: 0.26 },
  homeNav: { minHeight: 42, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: StyleSheet.hairlineWidth, paddingBottom: 10 },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  brandLabel: { fontSize: 11, letterSpacing: 2.5, fontFamily: 'Inter_400Regular' },
  controls: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  onlinePill: { minHeight: 32, flexDirection: 'row', alignItems: 'center', gap: 6, borderRadius: 18, paddingHorizontal: 10 },
  onlineDot: { width: 6, height: 6, borderRadius: 3 },
  onlineLabel: { fontSize: 11, fontFamily: 'Inter_400Regular' },
  firmButton: { minHeight: 32, justifyContent: 'center', paddingHorizontal: 10, borderRadius: 8 },
  firmButtonLabel: { color: '#ffffff', fontSize: 11, fontFamily: 'Inter_500Medium' },
  firmBadge: { borderWidth: 1, borderRadius: 14, paddingVertical: 3, paddingHorizontal: 8 },
  firmBadgeText: { fontSize: 9, letterSpacing: 0.6, fontFamily: 'Inter_600SemiBold' },
  greetingBlock: { paddingTop: 23, paddingBottom: 18 },
  greeting: { fontSize: 31, lineHeight: 37, letterSpacing: -0.5, fontFamily: 'Inter_600SemiBold' },
  greetingSub: { fontSize: 16, lineHeight: 23, marginTop: 3, fontFamily: 'Inter_400Regular' },
  storageWarning: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, padding: 12, borderRadius: 14, marginBottom: 14 },
  storageWarningText: { flex: 1, fontSize: 12, lineHeight: 18, fontFamily: 'Inter_400Regular' },
  projectsHeader: { minHeight: 30, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 11 },
  sectionLabel: { fontSize: 11, letterSpacing: 0.7, fontFamily: 'Inter_600SemiBold' },
  queuePill: { minHeight: 27, borderRadius: 15, flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 9 },
  queueLabel: { fontSize: 10, fontFamily: 'Inter_500Medium' },
  projectPressable: { marginBottom: 12 },
  projectCard: { borderRadius: 18 },
  projectTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 7, gap: 8 },
  projectName: { flex: 1, fontSize: 17, lineHeight: 22, letterSpacing: -0.35, fontFamily: 'Inter_600SemiBold' },
  scopeBadge: { borderWidth: 1, borderRadius: 18, paddingHorizontal: 10, paddingVertical: 3 },
  scopeBadgeText: { fontSize: 11, fontFamily: 'Inter_600SemiBold' },
  projectState: { fontSize: 15, lineHeight: 22, marginBottom: 11, fontFamily: 'Inter_400Regular' },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 5 },
  tag: { borderWidth: 1, borderRadius: 18, paddingVertical: 3, paddingHorizontal: 9 },
  tagText: { fontSize: 11, fontFamily: 'Inter_400Regular' },
  projectFlash: { marginTop: 11, paddingTop: 10, borderTopWidth: StyleSheet.hairlineWidth },
  projectFlashText: { fontSize: 12, lineHeight: 17, fontFamily: 'Inter_400Regular' },
  intentDock: { position: 'absolute', left: 0, right: 0, borderTopWidth: StyleSheet.hairlineWidth, paddingHorizontal: 22, paddingTop: 7 },
  dockStatusRow: { height: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'center' },
  intentStatus: { flex: 1, fontSize: 10, textAlign: 'center', fontFamily: 'Inter_400Regular' },
  refreshButton: { width: 24, height: 18, alignItems: 'center', justifyContent: 'center' },
  intentBar: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, borderRadius: 24, paddingVertical: 5, paddingLeft: 16, paddingRight: 6 },
  intentInput: { flex: 1, fontSize: 15, lineHeight: 21, paddingVertical: 4, fontFamily: 'Inter_400Regular' },
  micButton: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
});
