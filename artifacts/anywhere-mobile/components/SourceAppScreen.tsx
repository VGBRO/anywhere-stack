import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { WebView } from 'react-native-webview';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { sourceAppUrl } from '@/constants/sourceApp';
import colors from '@/constants/colors';

// Render the repository's actual interface, not a separately redesigned copy.
export default function SourceAppScreen() {
  const [attempt, setAttempt] = useState(0);
  const insets = useSafeAreaInsets();

  if (!sourceAppUrl) {
    return (
      <View style={styles.message}>
        <Text style={styles.error}>The Anywhere Stack server address is missing.</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      <WebView
        key={attempt}
        testID="original-anywhere-stack"
        source={{ uri: sourceAppUrl }}
        style={styles.container}
        javaScriptEnabled
        domStorageEnabled
        startInLoadingState
        allowsInlineMediaPlayback
        mediaCapturePermissionGrantType="grantIfSameHostElsePrompt"
        contentInsetAdjustmentBehavior="never"
        renderLoading={() => (
          <View style={styles.loading}>
            <ActivityIndicator color={colors.light.primary} />
          </View>
        )}
        renderError={() => (
          <View style={styles.message}>
            <Text style={styles.error}>Unable to load Anywhere Stack.</Text>
            <Pressable
              accessibilityRole="button"
              testID="retry-source-app"
              onPress={() => setAttempt(value => value + 1)}
              style={styles.retry}
            >
              <Text style={styles.retryText}>Retry</Text>
            </Pressable>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.light.background },
  loading: {
    ...StyleSheet.absoluteFill,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.light.background,
  },
  message: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 20,
    backgroundColor: colors.light.background,
  },
  error: { color: colors.light.text, textAlign: 'center', fontSize: 16 },
  retry: { backgroundColor: colors.light.primary, paddingHorizontal: 24, paddingVertical: 12, borderRadius: 24 },
  retryText: { color: colors.light.primaryForeground, fontSize: 16 },
});
