import { Feather } from '@expo/vector-icons';
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useColors } from '@/hooks/useColors';

type SpeechAlternative = { transcript: string };
type SpeechResult = ArrayLike<SpeechAlternative> & { isFinal: boolean };
type SpeechRecognitionEvent = { resultIndex: number; results: ArrayLike<SpeechResult> };
type SpeechRecognitionInstance = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};
type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;
type WindowWithSpeech = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

export function VoiceCaptureModal({
  visible,
  onClose,
  onSubmit,
}: {
  visible: boolean;
  onClose: () => void;
  onSubmit: (text: string) => Promise<void> | void;
}) {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const [text, setText] = useState('');
  const [transcript, setTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const [message, setMessage] = useState('Speak naturally. Stack is listening.');
  const recognition = useRef<SpeechRecognitionInstance | null>(null);
  const busy = listening;

  useEffect(
    () => () => {
      try {
        recognition.current?.stop();
      } catch {
        // Speech recognition may already be stopped by the browser.
      }
    },
    [],
  );

  const startListening = () => {
    const speechWindow =
      typeof window === 'undefined' ? undefined : (window as WindowWithSpeech);
    const SpeechRecognition = speechWindow?.SpeechRecognition ?? speechWindow?.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessage('Use your keyboard’s microphone to dictate, or type below.');
      return;
    }
    try {
      const instance = new SpeechRecognition();
      recognition.current = instance;
      instance.lang = 'en-US';
      instance.continuous = false;
      instance.interimResults = true;
      instance.onresult = (event) => {
        const next = Array.from(event.results)
          .slice(event.resultIndex)
          .map((result) => result[0]?.transcript ?? '')
          .join(' ')
          .trim();
        if (next) {
          setTranscript(next);
          setText(next);
          setMessage('Listening…');
        }
      };
      instance.onerror = () => {
        setListening(false);
        setMessage('Microphone unavailable. Type your intent below.');
      };
      instance.onend = () => setListening(false);
      setTranscript('');
      setMessage('Listening…');
      setListening(true);
      instance.start();
    } catch {
      setListening(false);
      setMessage('Microphone unavailable. Type your intent below.');
    }
  };

  const stopListening = () => {
    try {
      recognition.current?.stop();
    } catch {
      setListening(false);
    }
  };

  const submit = async () => {
    const intent = (text || transcript).trim();
    if (!intent) {
      setMessage('Speak or type an intent before sending.');
      return;
    }
    stopListening();
    await onSubmit(intent);
    setText('');
    setTranscript('');
  };

  const close = () => {
    stopListening();
    setText('');
    setTranscript('');
    setMessage('Speak naturally. Stack is listening.');
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="fade"
      transparent
      statusBarTranslucent
      onRequestClose={close}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.overlay}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Close voice capture"
          onPress={close}
          style={[styles.closeButton, { top: Math.max(insets.top, 18) + 22 }]}
        >
          <Feather name="x" size={20} color="#1d1d1f" />
        </Pressable>

        <View style={styles.center}>
          <Text style={[styles.state, { color: listening ? colors.tint : 'rgba(255,255,255,0.45)' }]}>
            {listening ? 'LISTENING' : transcript ? 'READY' : 'VOICE CAPTURE'}
          </Text>
          <View style={styles.stillPoint}>
            <View style={[styles.ring, styles.ringOne, listening && styles.ringActive]} />
            <View style={[styles.ring, styles.ringTwo, listening && styles.ringActive]} />
            <View style={[styles.ring, styles.ringThree, listening && styles.ringActive]} />
            <View style={[styles.core, listening && { backgroundColor: colors.tint }]} />
          </View>
          <Text style={styles.transcript}>
            {transcript ? '“' + transcript + '”' : 'Speak naturally. Stack is listening.'}
          </Text>
          <Text style={[styles.message, { color: colors.mutedForeground }]}>{message}</Text>
          <Pressable
            accessibilityRole="button"
            onPress={listening ? stopListening : startListening}
            style={({ pressed }) => [
              styles.listenButton,
              { backgroundColor: colors.glassSurface, opacity: pressed ? 0.75 : 1 },
            ]}
          >
            <Feather name={listening ? 'square' : 'mic'} size={15} color={colors.foreground} />
            <Text style={[styles.listenLabel, { color: colors.foreground }]}>
              {listening ? 'Stop listening' : 'Start listening'}
            </Text>
          </Pressable>
        </View>

        <View style={[styles.inputRow, { bottom: Math.max(insets.bottom, 20) + 12 }]}>
          <TextInput
            testID="voice-intent-input"
            accessibilityLabel="Type an intent"
            value={text}
            onChangeText={(value) => {
              setText(value);
              setTranscript('');
            }}
            onSubmitEditing={() => void submit()}
            placeholder="Or type here…"
            placeholderTextColor="rgba(255,255,255,0.42)"
            returnKeyType="send"
            blurOnSubmit
            style={styles.voiceInput}
          />
          <Pressable
            testID="voice-send"
            accessibilityRole="button"
            accessibilityLabel="Send voice intent"
            disabled={busy}
            onPress={() => void submit()}
            style={({ pressed }) => [styles.sendButton, { backgroundColor: colors.primary, opacity: busy ? 0.5 : pressed ? 0.82 : 1 }]}
          >
            {busy ? (
              <ActivityIndicator size="small" color={colors.primaryForeground} />
            ) : (
              <Feather name="arrow-up-right" size={17} color={colors.primaryForeground} />
            )}
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.88)', justifyContent: 'center' },
  closeButton: {
    position: 'absolute',
    right: 22,
    zIndex: 2,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(210,210,215,0.64)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  center: { alignItems: 'center', paddingHorizontal: 30, marginTop: -70 },
  state: { fontSize: 11, letterSpacing: 2.2, fontFamily: 'Inter_500Medium', marginBottom: 34 },
  stillPoint: { width: 112, height: 112, alignItems: 'center', justifyContent: 'center', marginBottom: 34 },
  ring: { position: 'absolute', borderWidth: 1, borderRadius: 100, borderColor: 'rgba(255,255,255,0.24)' },
  ringOne: { width: 26, height: 26 },
  ringTwo: { width: 62, height: 62 },
  ringThree: { width: 104, height: 104 },
  ringActive: { borderColor: 'rgba(41,151,255,0.7)' },
  core: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#ffffff' },
  transcript: { minHeight: 52, maxWidth: 290, color: 'rgba(255,255,255,0.86)', fontSize: 16, lineHeight: 24, textAlign: 'center', fontFamily: 'Inter_400Regular' },
  message: { marginTop: 7, textAlign: 'center', fontSize: 12, lineHeight: 18, fontFamily: 'Inter_400Regular' },
  listenButton: { minHeight: 40, paddingHorizontal: 15, borderRadius: 22, flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 24 },
  listenLabel: { fontSize: 12, fontFamily: 'Inter_500Medium' },
  inputRow: { position: 'absolute', left: 22, right: 22, flexDirection: 'row', alignItems: 'center', gap: 9 },
  voiceInput: { flex: 1, minHeight: 46, paddingHorizontal: 17, borderRadius: 24, borderWidth: 1, borderColor: 'rgba(255,255,255,0.18)', backgroundColor: 'rgba(255,255,255,0.1)', color: '#ffffff', fontSize: 15, fontFamily: 'Inter_400Regular' },
  sendButton: { width: 46, height: 46, borderRadius: 23, alignItems: 'center', justifyContent: 'center' },
});
