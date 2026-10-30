import { Stack } from 'expo-router';

// The upstream interface owns its navigation; do not add a second tab bar.
export default function SourceAppLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
