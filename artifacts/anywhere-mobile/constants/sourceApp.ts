// Mobile uses its own exact upstream snapshot, without replacing the web UI.
// Expo injects this domain for development previews and production builds.
const domain = process.env.EXPO_PUBLIC_DOMAIN;

export const sourceAppUrl = domain ? `https://${domain}/mobile-source.html?source=00ef0ce` : null;
