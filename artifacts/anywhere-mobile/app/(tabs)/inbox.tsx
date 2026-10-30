import { Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Platform,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Atmosphere, GlassPanel } from '@/components/Atmosphere';
import { useProjectStack } from '@/context/ProjectContext';
import { useColors } from '@/hooks/useColors';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function InboxScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const {
    queue,
    liveAIReady,
    checkingConnection,
    busy,
    refreshConnection,
    retryQueue,
  } = useProjectStack();
  const [message, setMessage] = useState<string | null>(null);

  const retry = async () => {
    if (busy) return;
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const result = await retryQueue();
    setMessage(result.message);
  };

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <Atmosphere />
      <FlatList
        data={queue}
        keyExtractor={(item) => item.id}
        scrollEnabled={queue.length > 0}
        contentContainerStyle={{
          flexGrow: 1,
          paddingTop: (Platform.OS === 'web' ? 67 : insets.top) + 22,
          paddingHorizontal: 22,
          paddingBottom: Math.max(insets.bottom, Platform.OS === 'web' ? 34 : 18) + 100,
        }}
        refreshControl={
          <RefreshControl
            refreshing={checkingConnection}
            onRefresh={() => void refreshConnection()}
            tintColor={colors.primary}
          />
        }
        ListHeaderComponent={
          <View>
            <View style={styles.eyebrow}>
              <Feather name="inbox" size={14} color={colors.primary} />
              <Text style={[styles.eyebrowText, { color: colors.mutedForeground }]}>INTENT INBOX</Text>
            </View>
            <Text style={[styles.title, { color: colors.foreground }]}>Waiting for a signal.</Text>
            <Text style={[styles.subtitle, { color: colors.mutedForeground }]}>
              Captured thoughts stay here until live AI is available.
            </Text>
            {queue.length > 0 ? (
              <GlassPanel style={styles.summary}>
                <View style={styles.summaryRow}>
                  <View style={[styles.countBadge, { backgroundColor: colors.glassStrong }]}>
                    <Text style={[styles.count, { color: colors.primary }]}>{queue.length}</Text>
                  </View>
                  <View style={styles.summaryTextWrap}>
                    <Text style={[styles.summaryTitle, { color: colors.foreground }]}>
                      Saved on this device
                    </Text>
                    <Text style={[styles.summaryDetail, { color: colors.mutedForeground }]}>
                      {liveAIReady ? 'Ready to send through Nemotron' : 'Will remain here until live AI is ready'}
                    </Text>
                  </View>
                  <Pressable
                    testID="retry-intents"
                    accessibilityRole="button"
                    accessibilityLabel="Retry pending intents"
                    onPress={() => void retry()}
                    disabled={busy || !liveAIReady}
                    style={({ pressed }) => [
                      styles.retryButton,
                      {
                        backgroundColor: colors.primary,
                        opacity: busy || !liveAIReady ? 0.48 : pressed ? 0.78 : 1,
                      },
                    ]}
                  >
                    {busy ? (
                      <ActivityIndicator color={colors.primaryForeground} size="small" />
                    ) : (
                      <Feather name="refresh-cw" size={16} color={colors.primaryForeground} />
                    )}
                  </Pressable>
                </View>
              </GlassPanel>
            ) : null}
            {message ? (
              <Text accessibilityLiveRegion="polite" style={[styles.feedback, { color: colors.mutedForeground }]}>
                {message}
              </Text>
            ) : null}
            {queue.length > 0 ? (
              <Text style={[styles.sectionTitle, { color: colors.mutedForeground }]}>SAVED INTENTS</Text>
            ) : null}
          </View>
        }
        ListEmptyComponent={
          <GlassPanel style={styles.emptyPanel}>
            <View style={[styles.emptyIcon, { backgroundColor: colors.accent }]}>
              <Feather name="check" size={19} color={colors.primary} />
            </View>
            <Text style={[styles.emptyTitle, { color: colors.foreground }]}>All caught up.</Text>
            <Text style={[styles.emptyText, { color: colors.mutedForeground }]}>
              Thoughts captured offline will appear here, ready to continue when you reconnect.
            </Text>
          </GlassPanel>
        }
        renderItem={({ item }) => (
          <GlassPanel style={styles.intentCard}>
            <View style={styles.intentHeader}>
              <Text style={[styles.intentDate, { color: colors.mutedForeground }]}>
                {new Date(item.createdAt).toLocaleString([], {
                  month: 'short',
                  day: 'numeric',
                  hour: 'numeric',
                  minute: '2-digit',
                })}
              </Text>
              <View style={[styles.pendingBadge, { backgroundColor: colors.accent }]}>
                <Text style={[styles.pendingText, { color: colors.accentForeground }]}>Waiting</Text>
              </View>
            </View>
            <Text style={[styles.intentText, { color: colors.foreground }]}>{item.text}</Text>
          </GlassPanel>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  eyebrow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  eyebrowText: { fontSize: 11, letterSpacing: 1.7, fontFamily: 'Inter_600SemiBold' },
  title: { fontSize: 31, lineHeight: 38, letterSpacing: -1.05, fontFamily: 'Inter_600SemiBold' },
  subtitle: { fontSize: 15, lineHeight: 22, marginTop: 8, marginBottom: 24, fontFamily: 'Inter_400Regular' },
  summary: { marginBottom: 18 },
  summaryRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  countBadge: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  count: { fontSize: 17, fontFamily: 'Inter_600SemiBold' },
  summaryTextWrap: { flex: 1 },
  summaryTitle: { fontSize: 14, fontFamily: 'Inter_600SemiBold' },
  summaryDetail: { fontSize: 11, lineHeight: 16, marginTop: 3, fontFamily: 'Inter_400Regular' },
  retryButton: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  feedback: { fontSize: 13, lineHeight: 19, marginBottom: 12, fontFamily: 'Inter_400Regular' },
  sectionTitle: { fontSize: 10, letterSpacing: 1.4, fontFamily: 'Inter_600SemiBold', marginBottom: 11 },
  emptyPanel: { marginTop: 12, alignItems: 'center', paddingVertical: 27 },
  emptyIcon: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  emptyTitle: { fontSize: 18, fontFamily: 'Inter_600SemiBold' },
  emptyText: { fontSize: 13, lineHeight: 19, marginTop: 7, textAlign: 'center', fontFamily: 'Inter_400Regular' },
  intentCard: { marginBottom: 10 },
  intentHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 11 },
  intentDate: { fontSize: 11, fontFamily: 'Inter_500Medium' },
  pendingBadge: { borderRadius: 12, paddingVertical: 4, paddingHorizontal: 8 },
  pendingText: { fontSize: 10, fontFamily: 'Inter_600SemiBold' },
  intentText: { fontSize: 15, lineHeight: 22, fontFamily: 'Inter_400Regular' },
});
