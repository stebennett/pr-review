import { useEffect } from "react";
import { Routes, Route, useSearchParams, useNavigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { useAuth } from "./hooks/useAuth";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { setAuthToken } from "./services/api";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";

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
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
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
