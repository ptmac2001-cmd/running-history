import client from './client';
import type {
  HRZone, MonthStat, PaceTrendPoint, PersonalRecord,
  SourceStat, StreakInfo, SummaryStats, YearStat,
} from '../types';

export const fetchSummary = async (): Promise<SummaryStats> => {
  const { data } = await client.get('/api/analytics/summary');
  return data;
};

export const fetchByYear = async (): Promise<YearStat[]> => {
  const { data } = await client.get('/api/analytics/by-year');
  return data;
};

export const fetchByMonth = async (year?: number): Promise<MonthStat[]> => {
  const { data } = await client.get('/api/analytics/by-month', { params: year ? { year } : {} });
  return data;
};

export const fetchPaceTrend = async (period = 'monthly', years = 5): Promise<PaceTrendPoint[]> => {
  const { data } = await client.get('/api/analytics/pace-trend', { params: { period, years } });
  return data;
};

export const fetchHRZones = async (maxHr = 190): Promise<HRZone[]> => {
  const { data } = await client.get('/api/analytics/hr-zones', { params: { max_hr: maxHr } });
  return data;
};

export const fetchPersonalRecords = async (): Promise<PersonalRecord[]> => {
  const { data } = await client.get('/api/analytics/personal-records');
  return data;
};

export const fetchStreak = async (): Promise<StreakInfo> => {
  const { data } = await client.get('/api/analytics/longest-streak');
  return data;
};

export const fetchSources = async (): Promise<SourceStat[]> => {
  const { data } = await client.get('/api/analytics/sources');
  return data;
};
