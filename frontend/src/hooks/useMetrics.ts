/** Custom hooks for metrics data fetching */

import { useQuery } from 'react-query';
import { getMetrics } from '../api/client';
import type { Metrics } from '../types';

export const useMetrics = () => {
  return useQuery<Metrics>(
    'metrics',
    getMetrics,
    {
      staleTime: 30000,
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );
};
