export type ProjectScope = 'personal' | 'work';

export interface ProjectUpdate {
  id: string;
  text: string;
  response?: string;
  createdAt: string;
}

export interface StackProject {
  id: string;
  name: string;
  scope: ProjectScope;
  tags: string[];
  goal: string;
  state: string;
  decision: string;
  actions: string[];
  memory: string;
  updates: ProjectUpdate[];
}

export const initialProjects: StackProject[] = [
  {
    id: 'adu',
    name: 'Backyard ADU',
    scope: 'personal',
    tags: ['real-estate', 'construction'],
    goal: 'Build a 1,200 sq ft ADU to generate $2,800/month in rental income.',
    state: 'Permit submitted Sept 14. City review in progress. Three contractor quotes received.',
    decision: 'JADU classification — saves $12K and three months on timeline. Locked Sept 1.',
    actions: [
      'Call Building & Safety — permit status #2026-ADU-04421',
      'Review Oakwood Construction invoice (due Oct 15)',
      'Schedule structural inspection with Carlos Mendez',
    ],
    memory: 'HOA approval not required — confirmed Aug 20. Contractor: Carlos Mendez, cmendez@oakwoodcon.com, 661-445-2200.',
    updates: [],
  },
  {
    id: 'india',
    name: 'India AI Infrastructure',
    scope: 'work',
    tags: ['policy', 'AI', 'research'],
    goal: "Publish analysis on India's position in the global AI infrastructure race.",
    state: 'Outline complete. Reviewing NVIDIA × Reliance partnership. Need GPU allocation data.',
    decision: 'Focus on sovereign compute angle — more differentiated than the talent narrative.',
    actions: ['Pull latest TRAI spectrum data', 'Interview IIT Delhi AI lab contact', 'Draft intro section'],
    memory: 'Key thesis: India builds compute before governance — opposite of EU. 3-year window for US partnerships.',
    updates: [],
  },
  {
    id: 'anywhere',
    name: 'Anywhere Stack',
    scope: 'work',
    tags: ['hackathon', 'AI', 'NVIDIA'],
    goal: 'Ship a working prototype and Loom demo for NVIDIA × Nebius Hackathon by Oct 30.',
    state: 'FastAPI live. Nemotron pipeline working. Apple atmospheric glass UI shipped. Recording on Replit.',
    decision: 'Lead with the Bira offline moment. KOA is the deeper story.',
    actions: ['Record Loom demo (3 min max)', 'Make repo public before deadline', 'Rotate exposed Nebius key'],
    memory: 'Built on Nemotron because Salesforce builds KOA on the same architecture. FirmOS = passport/visa trust.',
    updates: [],
  },
  {
    id: 'telugu',
    name: 'Telugu Thriller Script',
    scope: 'personal',
    tags: ['creative', 'writing'],
    goal: 'Complete 90-page feature script — psychological thriller, Hyderabad tech sector.',
    state: 'Act 1 complete (28 pages). Act 2 stalled at midpoint reversal.',
    decision: 'The protagonist is morally grey from page one. Structural choice is locked.',
    actions: ['Write midpoint betrayal reveal scene', 'Share Act 1 with writing group'],
    memory: 'Title: "The Architect." Tone: Andhadhun × Drishyam. Budget target: ₹8 crore.',
    updates: [],
  },
  {
    id: 'koa',
    name: 'KOA Positioning Brief',
    scope: 'work',
    tags: ['Salesforce', 'AI', 'strategy'],
    goal: 'Draft internal positioning on how KOA differentiates Salesforce AI.',
    state: 'Research phase. Mapping KOA tiers against GPT-4o and Claude Sonnet.',
    decision: 'Lead with enterprise trust, not benchmarks. CISOs buy on governance.',
    actions: [
      'Complete the competitive capability matrix',
      'Interview 2 AEs on objections',
      'Draft exec summary — 1 page',
    ],
    memory: 'KOA is built on Nemotron. Public information. Anywhere Stack is a live demo of KOA-style tiered routing.',
    updates: [],
  },
];
