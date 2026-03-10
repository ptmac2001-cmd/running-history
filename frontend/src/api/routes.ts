import client from './client';
import type { AllTracksResponse, RouteResponse } from '../types';

export const fetchActivityRoute = async (id: number): Promise<RouteResponse> => {
  const { data } = await client.get(`/api/routes/activity/${id}`);
  return data;
};

export const fetchAllTracks = async (year?: number, bbox?: string): Promise<AllTracksResponse> => {
  const params: Record<string, string | number> = {};
  if (year) params.year = year;
  if (bbox) params.bbox = bbox;
  const { data } = await client.get('/api/routes/all-tracks', { params });
  return data;
};
