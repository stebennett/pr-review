import { useState, useEffect, useCallback } from "react";
import { Navbar } from "../components/Navbar";
import { RepoList } from "../components/RepoList";
import { useOrganizations } from "../hooks/useOrganizations";
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

  return (
    <div className="min-h-screen">
      <Navbar
        organizations={organizations}
        selectedOrg={selectedOrg}
        onOrgSelect={handleOrgSelect}
        isLoadingOrgs={isLoading}
      />
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
