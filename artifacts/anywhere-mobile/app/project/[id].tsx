import { Feather } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import type { ComponentProps, ReactNode } from 'react';
import { useState } from 'react';
import {
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { GlassPanel } from '@/components/Atmosphere';
import { useProjectStack } from '@/context/ProjectContext';
import { useColors } from '@/hooks/useColors';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

function BrainSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: ComponentProps<typeof Feather>['name'];
  children: ReactNode;
}) {
  const colors = useColors();
  return (
    <GlassPanel style={styles.section}>
      <View style={styles.sectionHeading}>
        <Feather name={icon} size={15} color={colors.primary} />
        <Text style={[styles.sectionTitle, { color: colors.mutedForeground }]}>{title}</Text>
      </View>
      {children}
    </GlassPanel>
  );
}

const brainTabs = [
  { id: 'goal', label: 'Goal', title: 'INTENT', icon: 'target' },
  { id: 'state', label: 'State', title: 'CURRENT STATE', icon: 'activity' },
  { id: 'direction', label: 'Direction', title: 'DECISIONS', icon: 'git-commit' },
  { id: 'actions', label: 'Actions', title: 'NEXT ACTIONS', icon: 'arrow-up-right' },
  { id: 'memory', label: 'Memory', title: 'PERSISTENT MEMORY', icon: 'bookmark' },
] as const;
type BrainTab = (typeof brainTabs)[number]['id'];

export default function ProjectScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { id } = useLocalSearchParams<{ id: string }>();
  const projectId = Array.isArray(id) ? id[0] : id;
  const { getProject } = useProjectStack();
  const project = projectId ? getProject(projectId) : undefined;
  const [activeTab, setActiveTab] = useState<BrainTab>('goal');

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScrollView
        contentInsetAdjustmentBehavior="never"
        contentContainerStyle={{
          paddingTop: (Platform.OS === 'web' ? 67 : insets.top) + 10,
          paddingBottom: Math.max(insets.bottom, Platform.OS === 'web' ? 34 : 18) + 42,
          paddingHorizontal: 22,
        }}
      >
        <Pressable
          testID="back-to-projects"
          accessibilityRole="button"
          accessibilityLabel="Back"
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Feather name="arrow-left" size={19} color={colors.foreground} />
          <Text style={[styles.backLabel, { color: colors.foreground }]}>Projects</Text>
        </Pressable>

        {project ? (
          <>
            <View style={styles.titleBlock}>
              <View style={styles.titleRow}>
                <View style={[styles.scopeMark, { backgroundColor: colors.accent }]}>
                  <Feather
                    name={project.scope === 'work' ? 'briefcase' : 'compass'}
                    size={16}
                    color={colors.primary}
                  />
                </View>
                <Text style={[styles.scope, { color: colors.mutedForeground }]}>
                  {project.scope === 'work' ? 'WORK' : 'PERSONAL'}
                </Text>
              </View>
              <Text style={[styles.title, { color: colors.foreground }]}>{project.name}</Text>
              <View style={styles.tags}>
                {project.tags.map((tag) => (
                  <View key={tag} style={[styles.tag, { backgroundColor: colors.glassSurface, borderColor: colors.border }]}>
                    <Text style={[styles.tagText, { color: colors.mutedForeground }]}>{tag}</Text>
                  </View>
                ))}
              </View>
            </View>

            <View style={styles.brainTabs}>
              {brainTabs.map((tab) => {
                const selected = activeTab === tab.id;
                return (
                  <Pressable
                    key={tab.id}
                    testID={`brain-tab-${tab.id}`}
                    accessibilityRole="tab"
                    accessibilityState={{ selected }}
                    onPress={() => setActiveTab(tab.id)}
                    style={[
                      styles.brainTab,
                      { backgroundColor: selected ? colors.primary : colors.card, borderColor: selected ? colors.primary : colors.border },
                    ]}
                  >
                    <Text style={[styles.brainTabLabel, { color: selected ? colors.primaryForeground : colors.mutedForeground }]}>
                      {tab.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <BrainSection
              title={brainTabs.find((tab) => tab.id === activeTab)?.title ?? 'PROJECT BRAIN'}
              icon={brainTabs.find((tab) => tab.id === activeTab)?.icon ?? 'target'}
            >
              {activeTab === 'goal' ? (
                <Text style={[styles.bodyText, { color: colors.foreground }]}>{project.goal || 'No goal recorded yet.'}</Text>
              ) : activeTab === 'state' ? (
                <Text style={[styles.bodyText, { color: colors.foreground }]}>{project.state || 'No current state recorded yet.'}</Text>
              ) : activeTab === 'direction' ? (
                <Text style={[styles.bodyText, { color: colors.foreground }]}>{project.decision || 'No decisions recorded yet.'}</Text>
              ) : activeTab === 'actions' ? (
                project.actions.length ? (
                  project.actions.map((action, index) => (
                    <View key={`${index}-${action}`} style={styles.actionRow}>
                      <View style={[styles.actionDot, { backgroundColor: colors.primary }]} />
                      <Text style={[styles.bodyText, styles.actionText, { color: colors.foreground }]}>{action}</Text>
                    </View>
                  ))
                ) : (
                  <Text style={[styles.bodyText, { color: colors.mutedForeground }]}>No next actions recorded yet.</Text>
                )
              ) : (
                <Text style={[styles.bodyText, { color: colors.foreground }]}>{project.memory || 'No persistent memory recorded yet.'}</Text>
              )}
            </BrainSection>
          </>
        ) : (
          <GlassPanel style={styles.missing}>
            <Text style={[styles.missingTitle, { color: colors.foreground }]}>Project not found</Text>
            <Text style={[styles.missingText, { color: colors.mutedForeground }]}>
              This project is not available on this device.
            </Text>
          </GlassPanel>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  backButton: { height: 44, flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 20 },
  backLabel: { fontSize: 14, fontFamily: 'Inter_500Medium' },
  titleBlock: { marginBottom: 18 },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 13 },
  scopeMark: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  scope: { fontSize: 10, letterSpacing: 1.35, fontFamily: 'Inter_600SemiBold' },
  title: { fontSize: 30, lineHeight: 36, letterSpacing: -0.9, fontFamily: 'Inter_600SemiBold' },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 14 },
  tag: { borderWidth: 1, borderRadius: 14, paddingHorizontal: 10, paddingVertical: 5 },
  tagText: { fontSize: 11, fontFamily: 'Inter_500Medium' },
  brainTabs: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 12 },
  brainTab: { minHeight: 34, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderRadius: 18, paddingHorizontal: 13 },
  brainTabLabel: { fontSize: 12, fontFamily: 'Inter_500Medium' },
  section: { marginBottom: 10 },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  sectionTitle: { fontSize: 10, letterSpacing: 1.2, fontFamily: 'Inter_600SemiBold' },
  bodyText: { fontSize: 14, lineHeight: 21, fontFamily: 'Inter_400Regular' },
  actionRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 11, marginBottom: 10 },
  actionDot: { width: 6, height: 6, borderRadius: 3, marginTop: 8 },
  actionText: { flex: 1 },
  updateItem: { paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth },
  updateText: { fontSize: 13, lineHeight: 19, fontFamily: 'Inter_400Regular' },
  updateDate: { fontSize: 10, marginTop: 4, fontFamily: 'Inter_400Regular' },
  captureButton: { height: 52, borderRadius: 26, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, marginTop: 9 },
  captureLabel: { fontSize: 14, fontFamily: 'Inter_600SemiBold' },
  missing: { marginTop: 14 },
  missingTitle: { fontSize: 17, fontFamily: 'Inter_600SemiBold' },
  missingText: { fontSize: 14, lineHeight: 20, marginTop: 6, fontFamily: 'Inter_400Regular' },
});
