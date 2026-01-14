import { OrgSelector } from "./OrgSelector";
import { useAuth } from "../hooks/useAuth";
import type { Organization } from "../types";

interface NavbarProps {
  organizations: Organization[];
  selectedOrg: Organization | null;
  onOrgSelect: (org: Organization) => void;
  isLoadingOrgs?: boolean;
}

export function Navbar({
  organizations,
  selectedOrg,
  onOrgSelect,
  isLoadingOrgs = false,
}: NavbarProps) {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold text-gray-900">PR Review</h1>
            <OrgSelector
              organizations={organizations}
              selectedOrg={selectedOrg}
              onSelect={onOrgSelect}
              isLoading={isLoadingOrgs}
            />
          </div>
          <div className="flex items-center space-x-4">
            {/* Placeholder for refresh button (Task 4.8) */}
            <button
              type="button"
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
              title="Refresh"
            >
              <svg
                className="h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
            {user && (
              <>
                <div className="flex items-center space-x-2">
                  {user.avatar_url && (
                    <img
                      src={user.avatar_url}
                      alt={user.username}
                      className="h-8 w-8 rounded-full"
                    />
                  )}
                  <span className="text-sm text-gray-700">{user.username}</span>
                </div>
                <button
                  onClick={logout}
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  Sign out
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
