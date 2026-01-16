import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSettings, updateSettings } from "../services/api";
import type { UserSettings } from "../types";

export function useSettings() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const mutation = useMutation({
    mutationFn: (settings: { email: string }) => updateSettings(settings),
    onSuccess: (data: UserSettings) => {
      queryClient.setQueryData(["settings"], data);
    },
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateSettings: mutation.mutate,
    isUpdating: mutation.isPending,
    updateError: mutation.error,
    updateSuccess: mutation.isSuccess,
    resetUpdate: mutation.reset,
  };
}
