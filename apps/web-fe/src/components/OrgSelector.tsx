import { useState, useRef, useEffect } from "react";
import type { Organization } from "../types";

interface OrgSelectorProps {
  organizations: Organization[];
  selectedOrg: Organization | null;
  onSelect: (org: Organization) => void;
  isLoading?: boolean;
}

export function OrgSelector({
  organizations,
  selectedOrg,
  onSelect,
  isLoading = false,
}: OrgSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-500">
        <svg
          className="animate-spin h-4 w-4"
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
        <span>Loading organizations...</span>
      </div>
    );
  }

  if (organizations.length === 0) {
    return (
      <div className="px-3 py-2 text-sm text-gray-500">
        No organizations found
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        {selectedOrg ? (
          <>
            <img
              src={selectedOrg.avatar_url}
              alt={selectedOrg.login}
              className="h-5 w-5 rounded-full"
            />
            <span>{selectedOrg.login}</span>
          </>
        ) : (
          <span className="text-gray-500">Select organization</span>
        )}
        <svg
          className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {isOpen && (
        <ul
          className="absolute z-10 mt-1 w-full min-w-[200px] bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto focus:outline-none"
          role="listbox"
        >
          {organizations.map((org) => (
            <li
              key={org.id}
              role="option"
              aria-selected={selectedOrg?.id === org.id}
              className={`flex items-center space-x-2 px-3 py-2 cursor-pointer hover:bg-gray-100 ${
                selectedOrg?.id === org.id ? "bg-blue-50" : ""
              }`}
              onClick={() => {
                onSelect(org);
                setIsOpen(false);
              }}
            >
              <img
                src={org.avatar_url}
                alt={org.login}
                className="h-5 w-5 rounded-full"
              />
              <span className="text-sm text-gray-700">{org.login}</span>
              {selectedOrg?.id === org.id && (
                <svg
                  className="ml-auto h-4 w-4 text-blue-600"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
