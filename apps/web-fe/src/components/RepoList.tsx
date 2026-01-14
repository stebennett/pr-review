import { useState } from "react";
import { useRepositories } from "../hooks/useRepositories";
import { usePullRequests } from "../hooks/usePullRequests";
import { PullRequestCard } from "./PullRequestCard";
import type { Repository } from "../types";

interface RepoListProps {
  org: string;
}

interface RepositoryItemProps {
  org: string;
  repository: Repository;
  isExpanded: boolean;
  onToggle: () => void;
}

function RepositoryItem({
  org,
  repository,
  isExpanded,
  onToggle,
}: RepositoryItemProps) {
  const {
    data,
    isLoading: isLoadingPRs,
    error: prError,
  } = usePullRequests(isExpanded ? org : null, isExpanded ? repository.name : null);

  const pulls = data?.pulls ?? [];
  const prCount = pulls.length;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-gray-500 transition-transform duration-200">
            {isExpanded ? "▼" : "▶"}
          </span>
          <span className="font-medium text-gray-900">{repository.full_name}</span>
        </div>
        {isExpanded && isLoadingPRs ? (
          <span className="text-xs text-gray-500">Loading...</span>
        ) : (
          <span
            className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              prCount > 0
                ? "bg-blue-100 text-blue-800"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {prCount}
          </span>
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200 bg-gray-50">
          {isLoadingPRs ? (
            <div className="px-4 py-6 text-center">
              <svg
                className="animate-spin h-5 w-5 text-gray-500 mx-auto"
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
              <p className="mt-2 text-sm text-gray-500">Loading pull requests...</p>
            </div>
          ) : prError ? (
            <div className="px-4 py-6 text-center">
              <p className="text-sm text-red-600">
                Failed to load pull requests
              </p>
            </div>
          ) : pulls.length === 0 ? (
            <div className="px-4 py-6 text-center">
              <p className="text-sm text-gray-500">No open pull requests</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {pulls.map((pr) => (
                <PullRequestCard key={pr.number} pr={pr} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function RepoList({ org }: RepoListProps) {
  const { data: repositories = [], isLoading, error } = useRepositories(org);
  const [expandedRepos, setExpandedRepos] = useState<Set<string>>(new Set());

  const toggleRepo = (repoName: string) => {
    setExpandedRepos((prev) => {
      const next = new Set(prev);
      if (next.has(repoName)) {
        next.delete(repoName);
      } else {
        next.add(repoName);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="border border-gray-200 rounded-lg p-4 animate-pulse"
          >
            <div className="flex items-center justify-between">
              <div className="h-5 bg-gray-200 rounded w-1/3"></div>
              <div className="h-5 w-8 bg-gray-200 rounded-full"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Failed to load repositories</p>
        <p className="text-sm text-gray-500 mt-1">Please try again later</p>
      </div>
    );
  }

  if (repositories.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">No repositories found</p>
        <p className="text-sm text-gray-500 mt-1">
          This organization has no accessible repositories
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {repositories.map((repo) => (
        <RepositoryItem
          key={repo.id}
          org={org}
          repository={repo}
          isExpanded={expandedRepos.has(repo.name)}
          onToggle={() => toggleRepo(repo.name)}
        />
      ))}
    </div>
  );
}
