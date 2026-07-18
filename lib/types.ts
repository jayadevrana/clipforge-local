export type JobStage =
  | "queued"
  | "downloading"
  | "transcribing"
  | "analyzing"
  | "clipping"
  | "subtitling"
  | "exporting"
  | "verifying"
  | "completed"
  | "failed";

export type SubtitlePreset = "clean-minimal" | "bold-viral" | "creator-neon";

export interface JobMetadata {
  title?: string;
  channel?: string;
  thumbnail?: string;
  duration?: number;
  uploader?: string;
  webpageUrl?: string;
}

export interface VerificationReport {
  filename: string;
  duration: number;
  width: number;
  height: number;
  aspectRatioValid: boolean;
  audioStreamPresent: boolean;
  audioSimilarity?: number;
  subtitleBurnedIn: boolean;
  subtitleDiffScore?: number;
  playable: boolean;
  durationValid: boolean;
  resolutionValid: boolean;
  cleanBoundaries: boolean;
  importantTextPreserved?: boolean;
  layoutMode?: string;
  passed: boolean;
  notes: string[];
  verifiedAt?: string;
}

export interface ClipRecord {
  id: string;
  title: string;
  description?: string;
  start: number;
  end: number;
  duration: number;
  score: number;
  reasonTags: string[];
  subtitlePreset: SubtitlePreset;
  status: "pending" | "exporting" | "verified" | "failed";
  outputPath?: string;
  subtitlePath?: string;
  baseFilter?: string;
  baseFilterOutput?: string;
  finalFilter?: string;
  notes?: string[];
  boundaryNotes?: string[];
  layoutMode?: string;
  layoutNotes?: string[];
  layoutPath?: string;
  subtitleY?: number;
  titleY?: number;
  ocrProtectedBoxCount?: number;
  verification?: VerificationReport;
  createdAt: string;
  updatedAt: string;
}

export interface JobRecord {
  id: string;
  url: string;
  status: JobStage;
  progress: {
    stage: JobStage;
    message: string;
    percent: number;
  };
  createdAt: string;
  updatedAt: string;
  outputDir: string;
  sourceVideoPath?: string;
  transcriptPath?: string;
  transcriptPreview?: string;
  metadata?: JobMetadata;
  clips: ClipRecord[];
  failureReason?: string;
  logs?: string[];
}
