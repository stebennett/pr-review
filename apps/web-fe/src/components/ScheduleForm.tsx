import { useState, useEffect, useCallback } from "react";
import {
  previewPATOrganizations,
  previewPATRepositories,
  getScheduleOrganizations,
  getScheduleRepositories,
} from "../services/api";
import type {
  Schedule,
  ScheduleCreate,
  RepositoryRef,
  PATOrganization,
  PATRepository,
} from "../types";

interface ScheduleFormProps {
  schedule?: Schedule;
  onSave: (data: ScheduleCreate) => Promise<void>;
  onClose: () => void;
  isLoading?: boolean;
  error?: Error | null;
}

const CRON_EXAMPLES = [
  { label: "Weekdays at 9am", value: "0 9 * * 1-5" },
  { label: "Daily at 9am", value: "0 9 * * *" },
  { label: "Every Monday at 9am", value: "0 9 * * 1" },
  { label: "Twice daily (9am & 2pm)", value: "0 9,14 * * *" },
];

function isValidCronExpression(cron: string): boolean {
  const parts = cron.trim().split(/\s+/);
  return parts.length === 5;
}

type Step = 1 | 2 | 3;

export default function ScheduleForm({
  schedule,
  onSave,
  onClose,
  isLoading = false,
  error,
}: ScheduleFormProps) {
  const [step, setStep] = useState<Step>(1);

  // Step 1: Schedule details
  const [name, setName] = useState(schedule?.name ?? "");
  const [cronExpression, setCronExpression] = useState(
    schedule?.cron_expression ?? ""
  );
  const [isActive, setIsActive] = useState(schedule?.is_active ?? true);

  // Step 2: GitHub PAT
  const [githubPat, setGithubPat] = useState("");
  const [showPat, setShowPat] = useState(false);
  const [patUsername, setPatUsername] = useState<string | null>(null);
  const [isValidatingPat, setIsValidatingPat] = useState(false);
  const [patError, setPatError] = useState<string | null>(null);

  // Step 3: Repository selection
  const [organizations, setOrganizations] = useState<PATOrganization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
  const [repositories, setRepositories] = useState<PATRepository[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<RepositoryRef[]>(
    schedule?.repositories ?? []
  );
  const [isLoadingRepos, setIsLoadingRepos] = useState(false);
  const [repoError, setRepoError] = useState<string | null>(null);

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const loadRepositories = useCallback(
    async (org: string) => {
      setIsLoadingRepos(true);
      setRepoError(null);
      try {
        let repos: PATRepository[];
        if (githubPat) {
          // Use the new PAT provided in the form
          repos = await previewPATRepositories(githubPat, org);
        } else if (schedule?.id) {
          // Use the schedule's stored PAT
          repos = await getScheduleRepositories(schedule.id, org);
        } else {
          // No PAT available
          setRepoError("No PAT available to fetch repositories");
          setRepositories([]);
          return;
        }
        setRepositories(repos);
      } catch (err) {
        setRepoError(
          err instanceof Error ? err.message : "Failed to load repositories"
        );
        setRepositories([]);
      } finally {
        setIsLoadingRepos(false);
      }
    },
    [githubPat, schedule?.id]
  );

  // Load repos when organization changes in step 3
  useEffect(() => {
    if (step === 3 && selectedOrg && (githubPat || schedule?.id)) {
      loadRepositories(selectedOrg);
    }
  }, [selectedOrg, step, githubPat, schedule?.id, loadRepositories]);

  // Pre-select org if editing
  useEffect(() => {
    if (schedule?.repositories && schedule.repositories.length > 0 && organizations.length > 0) {
      const firstOrg = schedule.repositories[0].organization;
      if (organizations.some((o) => o.login === firstOrg)) {
        setSelectedOrg(firstOrg);
      }
    }
  }, [schedule?.repositories, organizations]);

  const validateStep1 = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = "Name is required";
    }

    if (!cronExpression.trim()) {
      newErrors.cronExpression = "Cron expression is required";
    } else if (!isValidCronExpression(cronExpression)) {
      newErrors.cronExpression =
        "Invalid cron expression. Must have 5 fields (minute hour day month weekday)";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = async (): Promise<boolean> => {
    // For new schedules, PAT is required
    if (!schedule && !githubPat.trim()) {
      setErrors({ githubPat: "GitHub Personal Access Token is required" });
      return false;
    }

    setIsValidatingPat(true);
    setPatError(null);
    setErrors({});

    try {
      let result: { organizations: PATOrganization[]; username: string };

      if (githubPat.trim()) {
        // Validate and use the new PAT
        result = await previewPATOrganizations(githubPat);
      } else if (schedule?.id) {
        // Use the schedule's stored PAT
        result = await getScheduleOrganizations(schedule.id);
      } else {
        setPatError("No PAT available");
        return false;
      }

      setOrganizations(result.organizations);
      setPatUsername(result.username);
      return true;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to validate PAT";
      setPatError(message);
      return false;
    } finally {
      setIsValidatingPat(false);
    }
  };

  const validateStep3 = (): boolean => {
    if (selectedRepos.length === 0) {
      setErrors({ repositories: "At least one repository must be selected" });
      return false;
    }
    setErrors({});
    return true;
  };

  const handleNext = async () => {
    if (step === 1) {
      if (validateStep1()) {
        setStep(2);
      }
    } else if (step === 2) {
      const isValid = await validateStep2();
      if (isValid) {
        setStep(3);
      }
    }
  };

  const handleBack = () => {
    if (step === 2) {
      setStep(1);
    } else if (step === 3) {
      setStep(2);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!validateStep3()) {
      return;
    }

    const data: ScheduleCreate = {
      name: name.trim(),
      cron_expression: cronExpression.trim(),
      github_pat: githubPat.trim() || "unchanged",
      repositories: selectedRepos,
      is_active: isActive,
    };

    // If editing and no new PAT provided, remove it from payload
    if (schedule && !githubPat.trim()) {
      delete (data as Partial<ScheduleCreate>).github_pat;
    }

    try {
      await onSave(data);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Failed to save schedule"
      );
    }
  };

  const handleRepoToggle = (repo: PATRepository) => {
    if (!selectedOrg) return;

    const repoRef: RepositoryRef = {
      organization: selectedOrg,
      repository: repo.name,
    };

    const isSelected = selectedRepos.some(
      (r) => r.organization === selectedOrg && r.repository === repo.name
    );

    if (isSelected) {
      setSelectedRepos(
        selectedRepos.filter(
          (r) => !(r.organization === selectedOrg && r.repository === repo.name)
        )
      );
    } else {
      setSelectedRepos([...selectedRepos, repoRef]);
    }

    if (errors.repositories) {
      setErrors((prev) => ({ ...prev, repositories: "" }));
    }
  };

  const isRepoSelected = (repoName: string): boolean => {
    return selectedRepos.some(
      (r) => r.organization === selectedOrg && r.repository === repoName
    );
  };

  const handleCronPreset = (value: string) => {
    setCronExpression(value);
    if (errors.cronExpression) {
      setErrors((prev) => ({ ...prev, cronExpression: "" }));
    }
  };

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-6">
      {[1, 2, 3].map((s) => (
        <div key={s} className="flex items-center">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              s === step
                ? "bg-blue-600 text-white"
                : s < step
                  ? "bg-green-500 text-white"
                  : "bg-gray-200 text-gray-600"
            }`}
          >
            {s < step ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              s
            )}
          </div>
          {s < 3 && (
            <div
              className={`w-12 h-1 mx-1 ${
                s < step ? "bg-green-500" : "bg-gray-200"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-4">
      <div>
        <label
          htmlFor="name"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Name
        </label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            if (errors.name) setErrors((prev) => ({ ...prev, name: "" }));
          }}
          placeholder="e.g., Daily PR Check"
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.name ? "border-red-300" : "border-gray-300"
          }`}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
        )}
      </div>

      <div>
        <label
          htmlFor="cronExpression"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Schedule (Cron Expression)
        </label>
        <input
          type="text"
          id="cronExpression"
          value={cronExpression}
          onChange={(e) => {
            setCronExpression(e.target.value);
            if (errors.cronExpression)
              setErrors((prev) => ({ ...prev, cronExpression: "" }));
          }}
          placeholder="0 9 * * 1-5"
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.cronExpression ? "border-red-300" : "border-gray-300"
          }`}
        />
        {errors.cronExpression && (
          <p className="mt-1 text-sm text-red-600">{errors.cronExpression}</p>
        )}
        <div className="mt-2 flex flex-wrap gap-2">
          {CRON_EXAMPLES.map((example) => (
            <button
              key={example.value}
              type="button"
              onClick={() => handleCronPreset(example.value)}
              className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded"
            >
              {example.label}
            </button>
          ))}
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Format: minute hour day month weekday.{" "}
          <a
            href="https://crontab.guru/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Learn more
          </a>
        </p>
      </div>

      <div className="flex items-center justify-between">
        <label
          htmlFor="isActive"
          className="text-sm font-medium text-gray-700"
        >
          Active
        </label>
        <button
          type="button"
          id="isActive"
          role="switch"
          aria-checked={isActive}
          onClick={() => setIsActive(!isActive)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            isActive ? "bg-blue-600" : "bg-gray-200"
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              isActive ? "translate-x-6" : "translate-x-1"
            }`}
          />
        </button>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-4">
      <div>
        <label
          htmlFor="githubPat"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          GitHub Personal Access Token
          {schedule && (
            <span className="font-normal text-gray-500">
              {" "}
              (leave blank to keep current)
            </span>
          )}
        </label>
        <div className="relative">
          <input
            type={showPat ? "text" : "password"}
            id="githubPat"
            value={githubPat}
            onChange={(e) => {
              setGithubPat(e.target.value);
              setPatError(null);
              if (errors.githubPat)
                setErrors((prev) => ({ ...prev, githubPat: "" }));
            }}
            placeholder={
              schedule ? "Enter new PAT or leave blank" : "ghp_xxxxxxxxxxxx"
            }
            className={`w-full px-3 py-2 pr-10 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.githubPat || patError ? "border-red-300" : "border-gray-300"
            }`}
            disabled={isValidatingPat}
          />
          <button
            type="button"
            onClick={() => setShowPat(!showPat)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            aria-label={showPat ? "Hide PAT" : "Show PAT"}
          >
            {showPat ? (
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                />
              </svg>
            ) : (
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
            )}
          </button>
        </div>
        {errors.githubPat && (
          <p className="mt-1 text-sm text-red-600">{errors.githubPat}</p>
        )}
        {patError && <p className="mt-1 text-sm text-red-600">{patError}</p>}
        <p className="mt-1 text-xs text-gray-500">
          Requires <code className="bg-gray-100 px-1">repo</code> and{" "}
          <code className="bg-gray-100 px-1">read:org</code> scopes
        </p>
      </div>

      {patUsername && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <p className="text-sm text-green-800">
            PAT validated for user: <strong>{patUsername}</strong>
          </p>
        </div>
      )}

      {schedule && !githubPat.trim() && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <p className="text-sm text-blue-800">
            Leave blank to use the existing stored token for repository selection.
            Enter a new PAT to replace it.
          </p>
        </div>
      )}
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Organization
        </label>
        <select
          value={selectedOrg ?? ""}
          onChange={(e) => {
            setSelectedOrg(e.target.value || null);
            setRepositories([]);
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoadingRepos}
        >
          <option value="">Select organization...</option>
          {organizations.map((org) => (
            <option key={org.id} value={org.login}>
              {org.login}
            </option>
          ))}
        </select>
      </div>

      {selectedOrg && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Repositories
          </label>
          <div
            className={`border rounded-md max-h-48 overflow-y-auto ${
              errors.repositories ? "border-red-300" : "border-gray-300"
            }`}
          >
            {isLoadingRepos ? (
              <div className="p-3 text-center text-gray-500">
                Loading repositories...
              </div>
            ) : repoError ? (
              <div className="p-3 text-center text-red-500">{repoError}</div>
            ) : repositories.length === 0 ? (
              <div className="p-3 text-center text-gray-500">
                No repositories found
              </div>
            ) : (
              repositories.map((repo) => (
                <label
                  key={repo.id}
                  className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={isRepoSelected(repo.name)}
                    onChange={() => handleRepoToggle(repo)}
                    className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{repo.name}</span>
                </label>
              ))
            )}
          </div>
        </div>
      )}

      {errors.repositories && (
        <p className="mt-1 text-sm text-red-600">{errors.repositories}</p>
      )}

      {selectedRepos.length > 0 && (
        <div>
          <p className="text-xs text-gray-600 mb-1">
            Selected ({selectedRepos.length}):
          </p>
          <div className="flex flex-wrap gap-1">
            {selectedRepos.map((repo) => (
              <span
                key={`${repo.organization}/${repo.repository}`}
                className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
              >
                {repo.organization}/{repo.repository}
                <button
                  type="button"
                  onClick={() =>
                    setSelectedRepos(
                      selectedRepos.filter(
                        (r) =>
                          !(
                            r.organization === repo.organization &&
                            r.repository === repo.repository
                          )
                      )
                    )
                  }
                  className="ml-1 text-blue-600 hover:text-blue-800"
                  aria-label={`Remove ${repo.organization}/${repo.repository}`}
                >
                  <svg
                    className="h-3 w-3"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-lg transform rounded-lg bg-white shadow-xl transition-all">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              {schedule ? "Edit Schedule" : "Create Schedule"}
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              {step === 1 && "Configure schedule timing"}
              {step === 2 && "Enter your GitHub Personal Access Token"}
              {step === 3 && "Select repositories to monitor"}
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="px-6 py-4">
              {renderStepIndicator()}

              {(error || submitError) && (
                <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-3">
                  <p className="text-sm text-red-700">
                    {submitError || error?.message || "An error occurred"}
                  </p>
                </div>
              )}

              {step === 1 && renderStep1()}
              {step === 2 && renderStep2()}
              {step === 3 && renderStep3()}
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
              <div>
                {step > 1 && (
                  <button
                    type="button"
                    onClick={handleBack}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                    disabled={isLoading || isValidatingPat}
                  >
                    Back
                  </button>
                )}
              </div>
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                  disabled={isLoading || isValidatingPat}
                >
                  Cancel
                </button>
                {step < 3 ? (
                  <button
                    type="button"
                    onClick={handleNext}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isValidatingPat}
                  >
                    {isValidatingPat ? "Validating..." : "Next"}
                  </button>
                ) : (
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isLoading}
                  >
                    {isLoading
                      ? "Saving..."
                      : schedule
                        ? "Save Changes"
                        : "Create Schedule"}
                  </button>
                )}
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
