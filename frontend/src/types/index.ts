export interface ActivitySummary {
  id: number;
  source: string;
  title: string | null;
  activity_type: string;
  start_time: string;
  duration_seconds: number;
  distance_miles: number;
  elevation_gain_feet: number | null;
  avg_pace_sec_per_mile: number | null;
  avg_heart_rate: number | null;
  calories: number | null;
  has_gps: boolean;
  start_lat: number | null;
  start_lng: number | null;
}

export interface LapSchema {
  lap_number: number;
  duration_seconds: number | null;
  distance_miles: number | null;
  avg_pace_sec_per_mile: number | null;
  avg_heart_rate: number | null;
  elevation_gain_ft: number | null;
}

export interface ActivityDetail extends ActivitySummary {
  moving_time_seconds: number | null;
  elevation_loss_feet: number | null;
  avg_speed_mph: number | null;
  max_speed_mph: number | null;
  max_heart_rate: number | null;
  avg_cadence: number | null;
  end_lat: number | null;
  end_lng: number | null;
  notes: string | null;
  gear_name: string | null;
  laps: LapSchema[];
}

export interface ActivityListResponse {
  items: ActivitySummary[];
  total: number;
  page: number;
  limit: number;
}

export interface RoutePoint {
  sequence: number;
  lat: number;
  lng: number;
  elevation_ft: number | null;
  heart_rate: number | null;
  cadence: number | null;
  speed_mph: number | null;
  distance_mi: number | null;
}

export interface RouteResponse {
  activity_id: number;
  points: RoutePoint[];
}

export interface TrackPolyline {
  activity_id: number;
  points: [number, number][];
}

export interface AllTracksResponse {
  tracks: TrackPolyline[];
}

export interface YearStat {
  year: number;
  runs: number;
  distance_miles: number;
  avg_pace_sec_per_mile: number | null;
  elevation_gain_ft: number | null;
}

export interface MonthStat {
  month: number;
  runs: number;
  distance_miles: number;
}

export interface PaceTrendPoint {
  period: string;
  avg_pace_sec_per_mile: number;
  run_count: number;
}

export interface HRZone {
  zone: number;
  label: string;
  seconds: number;
  percentage: number;
}

export interface PersonalRecord {
  distance_key: string;
  label: string;
  time_seconds: number;
  activity_id: number;
  set_at: string;
  formatted_time: string;
}

export interface StreakInfo {
  current_streak_days: number;
  longest_streak_days: number;
  longest_streak_start: string | null;
}

export interface SourceStat {
  source: string;
  count: number;
  earliest: string | null;
  latest: string | null;
}

export interface SummaryStats {
  total_runs: number;
  total_distance_miles: number;
  total_time_hours: number;
  total_elevation_ft: number;
  years_active: number;
  sources: string[];
}
