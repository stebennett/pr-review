import type { PullRequest } from "../types";
import { formatRelativeTime } from "../utils/date";

interface CheckStatusIconProps {
  status: PullRequest["checks_status"];
}

export function CheckStatusIcon({ status }: CheckStatusIconProps) {
  switch (status) {
    case "pass":
      return (
        <span className="text-green-600" title="Checks passed">
          ✓
        </span>
      );
    case "fail":
      return (
        <span className="text-red-600" title="Checks failed">
          ✗
        </span>
      );
    case "pending":
      return (
        <span className="text-yellow-600" title="Checks pending">
          ●
        </span>
      );
    default:
      return (
        <span className="text-gray-400" title="No checks">
          ○
        </span>
      );
  }
}

interface PullRequestCardProps {
  pr: PullRequest;
}

export function PullRequestCard({ pr }: PullRequestCardProps) {
  return (
    <div className="border-l-2 border-gray-200 pl-4 py-3 hover:bg-gray-50">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          <CheckStatusIcon status={pr.checks_status} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <a
              href={pr.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline truncate"
            >
              {pr.title}
            </a>
            <span className="text-xs text-gray-500 flex-shrink-0">
              {formatRelativeTime(pr.created_at)}
            </span>
          </div>
          {pr.labels.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {pr.labels.map((label) => (
                <span
                  key={label.name}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                  style={{
                    backgroundColor: `#${label.color}20`,
                    color: `#${label.color}`,
                    border: `1px solid #${label.color}40`,
                  }}
                >
                  {label.name}
                </span>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2 mt-1">
            <img
              src={pr.author.avatar_url}
              alt={pr.author.username}
              className="w-4 h-4 rounded-full"
            />
            <span className="text-xs text-gray-600">{pr.author.username}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
