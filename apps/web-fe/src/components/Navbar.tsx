import { Link } from "react-router-dom";
import { OrgSelector } from "./OrgSelector";
import { useAuth } from "../hooks/useAuth";
import type { Organization, RateLimitInfo } from "../types";
import { formatDistanceToNow } from "date-fns";

interface NavbarProps {
  organizations: Organization[];
  selectedOrg: Organization | null;
  onOrgSelect: (org: Organization) => void;
  isLoadingOrgs?: boolean;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  rateLimit?: RateLimitInfo | null;
}

function formatRateLimit(rateLimit: RateLimitInfo): string {
  const resetTime = new Date(rateLimit.reset_at);
  const resetIn = formatDistanceToNow(resetTime, { addSuffix: true });
  return `${rateLimit.remaining} requests remaining, resets ${resetIn}`;
}

export function Navbar({
  organizations,
  selectedOrg,
  onOrgSelect,
  isLoadingOrgs = false,
  onRefresh,
  isRefreshing = false,
  rateLimit,
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
            {rateLimit && (
              <span className="text-xs text-gray-500 hidden sm:inline">
                {formatRateLimit(rateLimit)}
              </span>
            )}
            <button
              type="button"
              onClick={onRefresh}
              disabled={isRefreshing || !onRefresh}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
              title={rateLimit ? formatRateLimit(rateLimit) : "Refresh"}
            >
              <svg
                className={`h-5 w-5 ${isRefreshing ? "animate-spin" : ""}`}
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
            <Link
              to="/settings"
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
              title="Settings"
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
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </Link>
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
