import axios from 'axios';

export const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Scene {
  id?: number;
  file_id: string;
  file_name?: string;
  storage_url?: string;
  file_type?: string;
  start_time: number;
  end_time: number;
  location: string;
  visual_description: string;
  tags: string[];
  mood: string;
  pacing: string;
  suitability: string[];
  relevance_score?: number;
}

export interface FileItem {
  file_id: string;
  file_name: string;
  file_type: 'video' | 'image';
  storage_url: string;
  duration_seconds: number;
  thumbnail_url?: string;
  parent_folder?: string;
  created_at?: string;
  analyzed_at?: string;
  scenes: Scene[];
}

export interface QueueTaskItem {
  id: number;
  file_id: string;
  file_name: string;
  file_type: string;
  status: 'PENDING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface ScriptSegmentMatch {
  segment_index: number;
  estimated_start: number;
  estimated_end: number;
  duration: number;
  narration_text: string;
  topic: string;
  visual_requirement: string;
  recommended_mood: string;
  matched_scenes: (Scene & { reason: string })[];
}

export interface ScriptAnalysisResult {
  total_estimated_duration: number;
  segments: ScriptSegmentMatch[];
  summary: string;
}

export interface AppSettings {
  google_drive_folder_id: string;
  composio_api_key_set: boolean;
  composio_api_key_masked: string;
  gemini_api_key_set: boolean;
  gemini_api_key_masked: string;
  polling_interval_minutes: number;
  auto_polling_enabled: boolean;
}
