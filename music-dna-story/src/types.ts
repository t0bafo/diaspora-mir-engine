export interface Track {
  file_name: string;
  genre: 'afrobeats' | 'amapiano' | 'afropiano';
  bpm: number;
  syncopation: number;
  pulse_clarity: number;
  complexity: number;
  log_drum: number;
  danceability: number;
  energy?: number;
  onset_rate?: number;
  backend?: string;
  run_label?: string;
  source?: string;
}

export interface MusicDNAData {
  version: string;
  total_tracks: number;
  genres: string[];
  hero_tracks: Track[];
  all_tracks: Track[];
}
