import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useSettings } from "../hooks/useSettings";
import { useSchedules } from "../hooks/useSchedules";
import ScheduleForm from "../components/ScheduleForm";
import type { Schedule, ScheduleCreate, ScheduleUpdate } from "../types";

function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export default function Settings() {
  const { user, logout } = useAuth();
  const {
    settings,
    isLoading,
    error,
    updateSettings,
    isUpdating,
    updateError,
    updateSuccess,
    resetUpdate,
  } = useSettings();

  const {
    schedules,
    isLoading: schedulesLoading,
    error: schedulesError,
    createSchedule,
    isCreating,
    createError,
    updateSchedule,
    isUpdating: isUpdatingSchedule,
    updateError: scheduleUpdateError,
  } = useSchedules();

  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);

  useEffect(() => {
    if (settings?.email) {
      setEmail(settings.email);
    }
  }, [settings?.email]);

  useEffect(() => {
    if (updateSuccess) {
      const timer = setTimeout(() => {
        resetUpdate();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [updateSuccess, resetUpdate]);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setEmailError(null);
    if (updateSuccess) {
      resetUpdate();
    }
  };

  const handleSaveEmail = () => {
    if (!email.trim()) {
      setEmailError("Email address is required");
      return;
    }
    if (!isValidEmail(email)) {
      setEmailError("Please enter a valid email address");
      return;
    }
    setEmailError(null);
    updateSettings({ email: email.trim() });
  };

  const handleOpenCreateForm = () => {
    setEditingSchedule(null);
    setShowScheduleForm(true);
  };

  const handleOpenEditForm = (schedule: Schedule) => {
    setEditingSchedule(schedule);
    setShowScheduleForm(true);
  };

  const handleCloseForm = () => {
    setShowScheduleForm(false);
    setEditingSchedule(null);
  };

  const handleSaveSchedule = async (data: ScheduleCreate) => {
    if (editingSchedule) {
      const updateData: ScheduleUpdate = {
        name: data.name,
        cron_expression: data.cron_expression,
        repositories: data.repositories,
        is_active: data.is_active,
      };
      if (data.github_pat && data.github_pat !== "unchanged") {
        updateData.github_pat = data.github_pat;
      }
      await updateSchedule(editingSchedule.id, updateData);
    } else {
      await createSchedule(data);
    }
    handleCloseForm();
  };

  return (
    <div className="min-h-screen">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link
                to="/"
                className="text-xl font-bold text-gray-900 hover:text-gray-700"
              >
                PR Review
              </Link>
              <span className="text-gray-400">/</span>
              <span className="text-lg text-gray-600">Settings</span>
            </div>
            <div className="flex items-center space-x-4">
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

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-8">Settings</h1>

        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4">
            <p className="text-sm text-red-700">
              Failed to load settings. Please try again.
            </p>
          </div>
        )}

        {isLoading ? (
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
            <p className="mt-4 text-gray-600">Loading settings...</p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Email Address Section */}
            <section className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Email Address
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                This email will be used for notification schedules.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="email"
                  value={email}
                  onChange={handleEmailChange}
                  placeholder="Enter your email address"
                  className={`flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    emailError ? "border-red-300" : "border-gray-300"
                  }`}
                  disabled={isUpdating}
                />
                <button
                  onClick={handleSaveEmail}
                  disabled={isUpdating}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUpdating ? "Saving..." : "Save"}
                </button>
              </div>
              {emailError && (
                <p className="mt-2 text-sm text-red-600">{emailError}</p>
              )}
              {updateError && (
                <p className="mt-2 text-sm text-red-600">
                  Failed to update email. Please try again.
                </p>
              )}
              {updateSuccess && (
                <p className="mt-2 text-sm text-green-600">
                  Email updated successfully.
                </p>
              )}
            </section>

            {/* Notification Schedules Section */}
            <section className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">
                  Notification Schedules
                </h2>
                <button
                  type="button"
                  onClick={handleOpenCreateForm}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                >
                  + Add Schedule
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Configure automated email notifications for pull request updates.
              </p>

              {schedulesError && (
                <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-3">
                  <p className="text-sm text-red-700">
                    Failed to load schedules. Please try again.
                  </p>
                </div>
              )}

              {schedulesLoading ? (
                <div className="text-center py-8">
                  <svg
                    className="animate-spin h-6 w-6 text-gray-600 mx-auto"
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
                </div>
              ) : schedules.length === 0 ? (
                <div className="border border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <p className="mt-4 text-gray-500">
                    No notification schedules configured yet.
                  </p>
                  <p className="mt-1 text-sm text-gray-400">
                    Create a schedule to receive regular email updates about open
                    pull requests.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {schedules.map((schedule) => (
                    <div
                      key={schedule.id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <h3 className="text-sm font-medium text-gray-900 truncate">
                              {schedule.name}
                            </h3>
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                schedule.is_active
                                  ? "bg-green-100 text-green-800"
                                  : "bg-gray-100 text-gray-800"
                              }`}
                            >
                              {schedule.is_active ? "Active" : "Inactive"}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-gray-500">
                            <code className="text-xs bg-gray-100 px-1 rounded">
                              {schedule.cron_expression}
                            </code>
                          </p>
                          <p className="mt-1 text-xs text-gray-400">
                            {schedule.repositories.length} repositor
                            {schedule.repositories.length === 1 ? "y" : "ies"}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleOpenEditForm(schedule)}
                          className="ml-4 text-sm text-blue-600 hover:text-blue-800"
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </main>

      {showScheduleForm && (
        <ScheduleForm
          schedule={editingSchedule ?? undefined}
          onSave={handleSaveSchedule}
          onClose={handleCloseForm}
          isLoading={isCreating || isUpdatingSchedule}
          error={createError || scheduleUpdateError}
        />
      )}
    </div>
  );
}
