import client from './client';
import type { ActivityDetail, ActivityListResponse } from '../types';

export interface ActivityFilters {
  page?: number;
  limit?: number;
  year?: number;
  month?: number;
  source?: string;
  activity_type?: string;
  min_distance_mi?: number;
  max_distance_mi?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export const fetchActivities = async (filters: ActivityFilters = {}): Promise<ActivityListResponse> => {
  const { data } = await client.get('/api/activities', { params: filters });
  return data;
};

export const fetchActivity = async (id: number): Promise<ActivityDetail> => {
  const { data } = await client.get(`/api/activities/${id}`);
  return data;
};

export const deleteActivity = async (id: number): Promise<void> => {
  await client.delete(`/api/activities/${id}`);
};
