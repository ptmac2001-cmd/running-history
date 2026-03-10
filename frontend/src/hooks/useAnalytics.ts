import { useQuery } from '@tanstack/react-query';
import { fetchSummary, fetchByYear, fetchByMonth, fetchPaceTrend, fetchHRZones, fetchPersonalRecords, fetchStreak, fetchSources } from '../api/analytics';

export const useSummary = () => useQuery({ queryKey: ['summary'], queryFn: fetchSummary });
export const useByYear = () => useQuery({ queryKey: ['by-year'], queryFn: fetchByYear });
export const useByMonth = (year?: number) => useQuery({ queryKey: ['by-month', year], queryFn: () => fetchByMonth(year) });
export const usePaceTrend = (period = 'monthly') => useQuery({ queryKey: ['pace-trend', period], queryFn: () => fetchPaceTrend(period) });
export const useHRZones = (maxHr = 190) => useQuery({ queryKey: ['hr-zones', maxHr], queryFn: () => fetchHRZones(maxHr) });
export const usePersonalRecords = () => useQuery({ queryKey: ['prs'], queryFn: fetchPersonalRecords });
export const useStreak = () => useQuery({ queryKey: ['streak'], queryFn: fetchStreak });
export const useSources = () => useQuery({ queryKey: ['sources'], queryFn: fetchSources });
