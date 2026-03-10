import { useQuery } from '@tanstack/react-query';
import { fetchActivities, fetchActivity, type ActivityFilters } from '../api/activities';

export const useActivities = (filters: ActivityFilters = {}) =>
  useQuery({
    queryKey: ['activities', filters],
    queryFn: () => fetchActivities(filters),
  });

export const useActivity = (id: number) =>
  useQuery({
    queryKey: ['activity', id],
    queryFn: () => fetchActivity(id),
    enabled: !!id,
  });
