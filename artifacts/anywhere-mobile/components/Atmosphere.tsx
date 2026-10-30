import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import Svg, {
  Circle,
  Defs,
  Ellipse,
  LinearGradient as SvgLinearGradient,
  Path,
  Rect,
  Stop,
} from 'react-native-svg';
import { Platform, StyleSheet, View, type ViewStyle } from 'react-native';
import type { ReactNode } from 'react';
import { useColors } from '@/hooks/useColors';

export function Atmosphere() {
  const colors = useColors();
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <LinearGradient
        colors={[colors.skyTop, '#2a5aa8', colors.skyMid, '#a8cce8', colors.skyBottom, '#f5f5f7']}
        locations={[0, 0.14, 0.3, 0.47, 0.58, 1]}
        style={StyleSheet.absoluteFill}
      />
      <View style={[styles.glow, { backgroundColor: '#fff2c5' }]} />
      <Svg
        width="100%"
        height="100%"
        viewBox="0 0 430 874"
        preserveAspectRatio="xMidYMid slice"
        style={StyleSheet.absoluteFill}
        fill="none"
      >
        <Defs>
          <SvgLinearGradient id="water" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor="#2e5090" />
            <Stop offset="0.4" stopColor={colors.water} />
            <Stop offset="1" stopColor="#142858" />
          </SvgLinearGradient>
          <SvgLinearGradient id="parchmentFade" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor="#f5f5f7" stopOpacity="0" />
            <Stop offset="1" stopColor="#f5f5f7" stopOpacity="1" />
          </SvgLinearGradient>
        </Defs>
        <Rect x="0" y="423" width="430" height="175" fill="url(#water)" />
        <Path
          d="M0 350 C34 322 62 329 94 309 C121 292 143 316 168 302 C199 285 207 322 236 301 C266 280 279 289 306 269 C334 249 347 285 372 270 C394 256 415 269 430 250 L430 423 L0 423 Z"
          fill={colors.horizonFar}
          fillOpacity={0.72}
        />
        <Path
          d="M0 355 C30 326 60 339 92 310 C126 280 142 324 173 299 C202 275 220 313 245 282 C273 247 294 302 321 277 C349 252 368 290 394 267 C409 253 421 255 430 248 L430 423 L0 423 Z"
          fill={colors.horizon}
          fillOpacity={0.9}
        />
        <Path
          d="M0 385 C34 365 62 379 90 348 C123 312 139 365 172 337 C201 311 224 367 255 331 C282 300 306 353 334 318 C365 281 386 343 430 291 L430 423 L0 423 Z"
          fill={colors.treeLine}
        />
        <Path d="M24 462 C82 450 147 468 207 456 C267 445 338 466 407 451" stroke="#b9d8f1" strokeOpacity={0.32} strokeWidth="1" />
        <Path d="M46 491 C112 483 177 500 254 486 C309 476 354 491 407 481" stroke="#b9d8f1" strokeOpacity={0.2} strokeWidth="1" />
        <Path d="M15 522 C75 515 128 526 193 518 C256 509 320 525 390 514" stroke="#b9d8f1" strokeOpacity={0.16} strokeWidth="1" />
        <Rect x="0" y="478" width="430" height="122" fill="url(#parchmentFade)" />
        <Rect x="0" y="598" width="430" height="276" fill="#f5f5f7" />
        <Circle cx="344" cy="64" r="116" fill="#fff2c5" fillOpacity={0.12} />
        <Circle cx="344" cy="64" r="52" fill="#fff2c5" fillOpacity={0.08} />
      </Svg>
    </View>
  );
}

export function OrbitalMark({ size = 34, color }: { size?: number; color?: string }) {
  const colors = useColors();
  const markColor = color ?? colors.foreground;
  return (
    <Svg width={size} height={size} viewBox="0 0 44 44" fill="none">
      <Ellipse
        cx="22"
        cy="22"
        rx="19"
        ry="7.5"
        stroke={markColor}
        strokeOpacity={0.78}
        strokeWidth="1.25"
        transform="rotate(-22 22 22)"
      />
      <Ellipse
        cx="22"
        cy="22"
        rx="19"
        ry="7.5"
        stroke={markColor}
        strokeOpacity={0.48}
        strokeWidth="1.25"
      />
      <Ellipse
        cx="22"
        cy="22"
        rx="19"
        ry="7.5"
        stroke={markColor}
        strokeOpacity={0.3}
        strokeWidth="1.25"
        transform="rotate(22 22 22)"
      />
      <Circle cx="22" cy="22" r="2.2" fill={markColor} />
    </Svg>
  );
}

export function GlassPanel({
  children,
  style,
  strong = false,
}: {
  children: ReactNode;
  style?: ViewStyle | ViewStyle[];
  strong?: boolean;
}) {
  const colors = useColors();
  return (
    <View
      style={[
        styles.panel,
        { borderColor: colors.glassBorder, backgroundColor: colors.glassSurface },
        style,
      ]}
    >
      {Platform.OS === 'ios' ? (
        <BlurView
          intensity={strong ? 38 : 24}
          tint={colors.background === '#091827' ? 'dark' : 'light'}
          style={styles.blur}
        >
          <View style={styles.content}>{children}</View>
        </BlurView>
      ) : (
        <View style={styles.content}>{children}</View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  glow: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    top: 62,
    right: -128,
    opacity: 0.22,
  },
  panel: {
    overflow: 'hidden',
    borderWidth: 1,
    borderRadius: 22,
  },
  blur: {
    flex: 1,
  },
  content: {
    padding: 18,
  },
});
