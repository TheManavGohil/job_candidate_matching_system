import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchJobs, fetchJob, uploadJob,
  fetchCandidates, fetchCandidate, uploadCandidates,
  parseResume, confirmCandidate,
  fetchMatchResults, fetchDetailedMatch,
} from '../api/client';
import type { ParsedResume } from '../api/client';

// ── Job Hooks ───────────────────────────────────────────────────────────────

export function useJobs() {
  return useQuery({ queryKey: ['jobs'], queryFn: fetchJobs });
}

export function useJob(jdId: string) {
  return useQuery({
    queryKey: ['job', jdId],
    queryFn: () => fetchJob(jdId),
    enabled: !!jdId,
  });
}

export function useUploadJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => uploadJob(formData),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

// ── Candidate Hooks ─────────────────────────────────────────────────────────

export function useCandidates() {
  return useQuery({ queryKey: ['candidates'], queryFn: fetchCandidates });
}

export function useCandidate(id: string) {
  return useQuery({
    queryKey: ['candidate', id],
    queryFn: () => fetchCandidate(id),
    enabled: !!id,
  });
}

export function useUploadCandidates() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => uploadCandidates(formData),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['candidates'] }),
  });
}

export function useParseResume() {
  return useMutation({
    mutationFn: (formData: FormData) => parseResume(formData),
  });
}

export function useConfirmCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (candidate: ParsedResume['candidate']) => confirmCandidate(candidate),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['candidates'] }),
  });
}

// ── Match Hooks ─────────────────────────────────────────────────────────────

export function useMatchResults(jdId: string, topK = 50, threshold = 0) {
  return useQuery({
    queryKey: ['match', jdId, topK, threshold],
    queryFn: () => fetchMatchResults(jdId, topK, threshold),
    enabled: !!jdId,
  });
}

export function useDetailedMatch(jdId: string, candidateId: string) {
  return useQuery({
    queryKey: ['match-detail', jdId, candidateId],
    queryFn: () => fetchDetailedMatch(jdId, candidateId),
    enabled: !!jdId && !!candidateId,
  });
}
