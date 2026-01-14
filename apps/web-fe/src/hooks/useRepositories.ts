import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import type { Repository, ApiResponse } from "../types";

interface RepositoriesData {
  repositories: Repository[];
}

export function useRepositories(org: string | null) {
  return useQuery({
    queryKey: ["repositories", org],
    queryFn: async () => {
      if (!org) {
        return [];
      }
      const response = await api.get<ApiResponse<RepositoriesData>>(
        `/api/organizations/${encodeURIComponent(org)}/repositories`
      );
      return response.data.repositories;
    },
    enabled: !!org,
  });
}
