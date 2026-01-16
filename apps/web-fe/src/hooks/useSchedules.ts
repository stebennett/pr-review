import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getSchedules,
  getSchedule,
  createSchedule,
  updateSchedule,
  deleteSchedule,
} from "../services/api";
import type { ScheduleCreate, ScheduleUpdate } from "../types";

export function useSchedules() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["schedules"],
    queryFn: getSchedules,
  });

  const createMutation = useMutation({
    mutationFn: (data: ScheduleCreate) => createSchedule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ScheduleUpdate }) =>
      updateSchedule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
    },
  });

  return {
    schedules: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    createSchedule: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    updateSchedule: (id: string, data: ScheduleUpdate) =>
      updateMutation.mutateAsync({ id, data }),
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,
    deleteSchedule: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,
  };
}

export function useSchedule(id: string | null) {
  return useQuery({
    queryKey: ["schedule", id],
    queryFn: () => (id ? getSchedule(id) : null),
    enabled: !!id,
  });
}
