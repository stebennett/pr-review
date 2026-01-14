import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import type { Organization, ApiResponse } from "../types";

interface OrganizationsData {
  organizations: Organization[];
}

export function useOrganizations() {
  return useQuery({
    queryKey: ["organizations"],
    queryFn: async () => {
      const response = await api.get<ApiResponse<OrganizationsData>>(
        "/api/organizations"
      );
      return response.data.organizations;
    },
  });
}
