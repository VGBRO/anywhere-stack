import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  useHealthCheck,
  useProcessIntent,
  useSyncQueue,
  type IntentResult,
  type Project as ApiProject,
  type QueueItem,
} from '@workspace/api-client-react';
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { initialProjects, type ProjectUpdate, type StackProject } from '@/data/projects';

const PROJECTS_KEY = '@anywhere-stack/projects-v1';
const QUEUE_KEY = '@anywhere-stack/intent-inbox-v1';

type PendingIntent = QueueItem & { createdAt: string };
export type IntentOutcome = {
  status: 'processed' | 'queued' | 'error';
  message: string;
  response?: string;
};
export type SyncOutcome = { processed: number; waiting: number; message: string };

type ProjectContextValue = {
  projects: StackProject[];
  queue: PendingIntent[];
  online: boolean;
  offlineMode: boolean;
  liveAIReady: boolean;
  firmMode: boolean;
  checkingConnection: boolean;
  busy: boolean;
  storageWarning: string | null;
  refreshConnection: () => Promise<void>;
  toggleConnection: () => Promise<string>;
  toggleFirmMode: () => void;
  getProject: (id: string) => StackProject | undefined;
  submitIntent: (text: string, projectId?: string) => Promise<IntentOutcome>;
  retryQueue: (ignoreManualOffline?: boolean) => Promise<SyncOutcome>;
};

const ProjectContext = createContext<ProjectContextValue | null>(null);

function readStatus(error: unknown): number | undefined {
  if (typeof error !== 'object' || error === null || !('status' in error)) return undefined;
  const value = (error as { status?: unknown }).status;
  return typeof value === 'number' ? value : undefined;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'The service could not process this intent.';
}

function addResult(projects: StackProject[], result: IntentResult, requestText: string): StackProject[] {
  const existing = projects.find((project) => project.id === result.project_id);
  const now = new Date().toISOString();
  const update: ProjectUpdate = {
    id: `${Date.now()}`,
    text: requestText,
    response: result.response,
    createdAt: now,
  };
  const brain = result.brain ?? {};

  if (existing) {
    return projects.map((project) =>
      project.id === existing.id
        ? {
            ...project,
            goal: brain.goal || project.goal,
            state: brain.state || project.state,
            decision: brain.decision || project.decision,
            actions: brain.actions?.length ? brain.actions : project.actions,
            memory: brain.memory || project.memory,
            updates: [update, ...project.updates].slice(0, 20),
          }
        : project,
    );
  }

  const newProject: StackProject = {
    id: result.project_id === 'new' ? `local-${Date.now()}` : result.project_id,
    name: result.project_name || 'New project',
    scope: 'personal',
    tags: [],
    goal: brain.goal || '',
    state: brain.state || 'Intent captured.',
    decision: brain.decision || '',
    actions: brain.actions || [],
    memory: brain.memory || '',
    updates: [update],
  };
  return [newProject, ...projects];
}

export function ProjectProvider({ children }: { children: ReactNode }) {
  const health = useHealthCheck({ query: { refetchInterval: 45_000, retry: 1 } });
  const intentMutation = useProcessIntent();
  const syncMutation = useSyncQueue();
  const [projects, setProjects] = useState<StackProject[]>(initialProjects);
  const [queue, setQueue] = useState<PendingIntent[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [manualOffline, setManualOffline] = useState(false);
  const [firmMode, setFirmMode] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function hydrate() {
      try {
        const [savedProjects, savedQueue] = await Promise.all([
          AsyncStorage.getItem(PROJECTS_KEY),
          AsyncStorage.getItem(QUEUE_KEY),
        ]);
        if (!cancelled && savedProjects) {
          const parsed: unknown = JSON.parse(savedProjects);
          if (Array.isArray(parsed)) setProjects(parsed as StackProject[]);
        }
        if (!cancelled && savedQueue) {
          const parsed: unknown = JSON.parse(savedQueue);
          if (Array.isArray(parsed)) setQueue(parsed as PendingIntent[]);
        }
      } catch {
        if (!cancelled) setStorageWarning('Saved device data could not be read. New changes may not persist.');
      } finally {
        if (!cancelled) setHydrated(true);
      }
    }
    void hydrate();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    void AsyncStorage.setItem(PROJECTS_KEY, JSON.stringify(projects)).catch(() => {
      setStorageWarning('Project changes are visible now but could not be saved on this device.');
    });
  }, [hydrated, projects]);

  useEffect(() => {
    if (!hydrated) return;
    void AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue)).catch(() => {
      setStorageWarning('The intent inbox could not be saved on this device.');
    });
  }, [hydrated, queue]);

  const serverOnline = health.isSuccess && !health.isError;
  const online = serverOnline && !manualOffline;
  const offlineMode = !online;
  const liveAIReady = online && health.data?.nebius_configured === true;
  const checkingConnection = health.isLoading || health.isFetching;
  const busy = intentMutation.isPending || syncMutation.isPending;

  const refreshConnection = useCallback(async () => {
    await health.refetch();
  }, [health]);

  const toggleFirmMode = useCallback(() => {
    setFirmMode((current) => !current);
  }, []);

  const getProject = useCallback(
    (id: string) => projects.find((project) => project.id === id),
    [projects],
  );

  const enqueue = useCallback(
    async (text: string, projectId?: string): Promise<void> => {
      const item: PendingIntent = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        text,
        project_id: projectId,
        createdAt: new Date().toISOString(),
      };
      const nextQueue = [item, ...queue];
      setQueue(nextQueue);
      try {
        await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(nextQueue));
      } catch {
        setStorageWarning('This intent could not be saved. Keep this screen open and try again.');
      }
    },
    [queue],
  );

  const submitIntent = useCallback(
    async (text: string, projectId?: string): Promise<IntentOutcome> => {
      const trimmed = text.trim();
      if (!trimmed) return { status: 'error', message: 'Write an intent before sending.' };
      if (manualOffline) {
        await enqueue(trimmed, projectId);
        return { status: 'queued', message: 'Captured offline — saved locally for retry.' };
      }
      const connection = await health.refetch();
      if (!connection.isSuccess || connection.data?.nebius_configured !== true) {
        await enqueue(trimmed, projectId);
        const message = connection.isSuccess
          ? 'Live AI is not configured on the server. This intent is saved on this device.'
          : 'The server is unreachable. This intent is saved on this device for retry.';
        return { status: 'queued', message };
      }

      const apiProjects: ApiProject[] = projects.map(({ id, name, tags, state, goal }) => ({
        id,
        name,
        tags,
        state,
        goal,
      }));
      try {
        const result = await intentMutation.mutateAsync({
          data: { text: trimmed, projects: apiProjects },
        });
        setProjects((current) => addResult(current, result, trimmed));
        return { status: 'processed', message: result.response, response: result.response };
      } catch (error) {
        const status = readStatus(error);
        if (status === 400) {
          return { status: 'error', message: errorMessage(error) };
        }
        await enqueue(trimmed, projectId);
        const message =
          status === 502 || status === 503
            ? `Live AI could not process this intent. It is saved on this device. ${errorMessage(error)}`
            : `The connection was interrupted. This intent is saved on this device. ${errorMessage(error)}`;
        return { status: 'queued', message };
      }
    },
    [enqueue, health, intentMutation, manualOffline, projects],
  );

  const retryQueue = useCallback(async (ignoreManualOffline = false): Promise<SyncOutcome> => {
    if (!queue.length) return { processed: 0, waiting: 0, message: 'Your intent inbox is clear.' };
    if (manualOffline && !ignoreManualOffline) {
      return {
        processed: 0,
        waiting: queue.length,
        message: 'Offline mode is on. Turn it off to retry these intents.',
      };
    }
    const connection = await health.refetch();
    if (!connection.isSuccess || connection.data?.nebius_configured !== true) {
      return {
        processed: 0,
        waiting: queue.length,
        message: connection.isSuccess
          ? 'Live AI is not configured yet. Your intents remain saved on this device.'
          : 'The server is still unreachable. Your intents remain saved on this device.',
      };
    }

    const apiProjects: ApiProject[] = projects.map(({ id, name, tags, state, goal }) => ({
      id,
      name,
      tags,
      state,
      goal,
    }));
    try {
      const response = await syncMutation.mutateAsync({
        data: {
          queue: queue.map(({ id, text, project_id }) => ({ id, text, project_id })),
          projects: apiProjects,
        },
      });
      const processedIds = new Set(
        response.results.filter((item) => item.status === 'processed').map((item) => item.id),
      );
      response.results.forEach((item) => {
        if (item.status === 'processed' && item.brain) {
          const intentResult = item as IntentResult;
          const originalText =
            queue.find((queued) => queued.id === item.id)?.text ??
            item.text ??
            item.response ??
            'Intent synced';
          setProjects((current) => addResult(current, intentResult, originalText));
        }
      });
      const remaining = queue.filter((item) => !processedIds.has(item.id));
      setQueue(remaining);
      await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(remaining));
      const processed = processedIds.size;
      return {
        processed,
        waiting: remaining.length,
        message:
          remaining.length > 0
            ? `${processed} intent${processed === 1 ? '' : 's'} processed. ${remaining.length} still waiting.`
            : `${processed} intent${processed === 1 ? '' : 's'} processed with live AI.`,
      };
    } catch (error) {
      return {
        processed: 0,
        waiting: queue.length,
        message: `Sync failed; your intents are still saved on this device. ${errorMessage(error)}`,
      };
    }
  }, [health, manualOffline, projects, queue, syncMutation]);

  const toggleConnection = useCallback(async () => {
    if (online) {
      setManualOffline(true);
      return 'Offline — intents will be saved locally.';
    }

    setManualOffline(false);
    const connection = await health.refetch();
    if (!connection.isSuccess || connection.isError) {
      return 'Still offline — your intents remain saved on this device.';
    }
    if (connection.data?.nebius_configured !== true) {
      return 'Connected. Live AI is unavailable, so new intents remain on this device.';
    }
    if (queue.length > 0) {
      const result = await retryQueue(true);
      return result.message;
    }
    return 'Connected. Your work is ready.';
  }, [health, online, queue.length, retryQueue]);

  const value = useMemo<ProjectContextValue>(
    () => ({
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
      getProject,
      submitIntent,
      retryQueue,
    }),
    [
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
      getProject,
      submitIntent,
      retryQueue,
    ],
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProjectStack() {
  const context = useContext(ProjectContext);
  if (!context) throw new Error('useProjectStack must be used inside ProjectProvider.');
  return context;
}
