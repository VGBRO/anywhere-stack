import React from 'react';
import { sourceAppUrl } from '@/constants/sourceApp';
import colors from '@/constants/colors';

export default function SourceAppScreen() {
  if (!sourceAppUrl) {
    return <div role="alert">The Anywhere Stack server address is missing.</div>;
  }

  return (
    <iframe
      title="Anywhere Stack"
      data-testid="original-anywhere-stack"
      src={sourceAppUrl}
      allow="microphone"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        border: 0,
        backgroundColor: colors.light.background,
      }}
    />
  );
}
