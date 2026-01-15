import { useState, useEffect, useCallback } from "react";
import { Navbar } from "../components/Navbar";
import { RepoList } from "../components/RepoList";
import { useOrganizations } from "../hooks/useOrganizations";
import { useRefresh } from "../hooks/useRefresh";
import type { Organization } from "../types";

const SELECTED_ORG_KEY = "pr-review-selected-org";

function getStoredOrg(): string | null {
  try {
    return localStorage.getItem(SELECTED_ORG_KEY);
  } catch {
    return null;
  }
}

function storeSelectedOrg(orgLogin: string): void {
  try {
    localStorage.setItem(SELECTED_ORG_KEY, orgLogin);
  } catch {
    // Ignore localStorage errors
  }
}

export default function Dashboard() {
  const { data: organizations = [], isLoading, error } = useOrganizations();
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const {
    refresh,
    isRefreshing,
    rateLimit,
    error: refreshError,
    clearError,
  } = useRefresh();

  // Restore selected org from localStorage when organizations load
  useEffect(() => {
    if (organizations.length > 0 && !selectedOrg) {
      const storedOrgLogin = getStoredOrg();
      if (storedOrgLogin) {
        const org = organizations.find((o) => o.login === storedOrgLogin);
        if (org) {
          setSelectedOrg(org);
          return;
        }
      }
      // If no stored org or stored org not found, select first one
      setSelectedOrg(organizations[0]);
      storeSelectedOrg(organizations[0].login);
    }
  }, [organizations, selectedOrg]);

  const handleOrgSelect = useCallback((org: Organization) => {
    setSelectedOrg(org);
    storeSelectedOrg(org.login);
  }, []);

  const handleRefresh = useCallback(async () => {
    clearError();
    await refresh();
  }, [refresh, clearError]);

  return (
    <div className="min-h-screen">
      <Navbar
        organizations={organizations}
        selectedOrg={selectedOrg}
        onOrgSelect={handleOrgSelect}
        isLoadingOrgs={isLoading}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
        rateLimit={rateLimit}
      />
      {refreshError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{refreshError}</p>
              </div>
            </div>
            <button
              onClick={clearError}
              className="text-red-400 hover:text-red-600"
            >
              <svg
                className="h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error ? (
          <div className="text-center py-12">
            <p className="text-red-600">
              Failed to load organizations. Please try again.
            </p>
          </div>
        ) : isLoading ? (
          <div className="text-center py-12">
            <svg
              className="animate-spin h-8 w-8 text-gray-600 mx-auto"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        ) : selectedOrg ? (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-medium text-gray-900">
                Repositories in {selectedOrg.login}
              </h2>
            </div>
            <RepoList org={selectedOrg.login} />
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600">
              Select an organization to view repositories.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
