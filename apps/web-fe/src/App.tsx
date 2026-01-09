import { useEffect } from "react";
import { Routes, Route, useSearchParams, useNavigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { useAuth } from "./hooks/useAuth";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { setAuthToken } from "./services/api";
import Login from "./pages/Login";

function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">PR Review</h1>
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <p className="text-gray-600">
            GitHub Pull Request monitoring application
          </p>
          <p className="text-sm text-green-600 mt-4">
            Welcome, {user?.username}! You are logged in.
          </p>
        </div>
      </main>
    </div>
  );
}

function TokenHandler({ children }: { children: React.ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { checkAuth } = useAuth();

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      // Store the token
      setAuthToken(token);
      // Remove token from URL
      searchParams.delete("token");
      setSearchParams(searchParams, { replace: true });
      // Re-check auth to load user
      checkAuth();
      // Navigate to dashboard
      navigate("/", { replace: true });
    }
  }, [searchParams, setSearchParams, navigate, checkAuth]);

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <TokenHandler>
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<Login />} />
      </Routes>
    </TokenHandler>
  );
}

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <AppRoutes />
      </div>
    </AuthProvider>
  );
}

export default App;
