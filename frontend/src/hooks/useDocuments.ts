/** Custom hooks for document data fetching */

import { useQuery, useMutation, useQueryClient } from 'react-query';
import { getDocuments, getDocument, deleteDocument, uploadDocument } from '../api/client';
import type { Document, DocumentDetail } from '../types';

export const useDocuments = (skip: number = 0, limit: number = 50, status?: string) => {
  return useQuery(
    ['documents', skip, limit, status],
    () => getDocuments(skip, limit, status),
    {
      staleTime: 30000,
    }
  );
};

export const useDocument = (id: string) => {
  return useQuery(
    ['document', id],
    () => getDocument(id),
    {
      enabled: !!id,
      staleTime: 30000,
    }
  );
};

export const useUploadDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation(uploadDocument, {
    onSuccess: () => {
      queryClient.invalidateQueries('documents');
    },
  });
};

export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation(deleteDocument, {
    onSuccess: () => {
      queryClient.invalidateQueries('documents');
    },
  });
};
