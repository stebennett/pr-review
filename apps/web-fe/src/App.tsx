import { useEffect } from "react";
import { Routes, Route, useSearchParams, useNavigate } from "react-router-dom";
import { setAuthToken } from "./services/api";
import Login from "./pages/Login";

function Dashboard() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">PR Review</h1>
        <p className="text-gray-600">
          GitHub Pull Request monitoring application
        </p>
        <p className="text-sm text-green-600 mt-4">You are logged in</p>
      </div>
    </div>
  );
}

function TokenHandler({ children }: { children: React.ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      // Store the token
      setAuthToken(token);
      // Remove token from URL
      searchParams.delete("token");
      setSearchParams(searchParams, { replace: true });
      // Navigate to dashboard
      navigate("/", { replace: true });
    }
  }, [searchParams, setSearchParams, navigate]);

  return <>{children}</>;
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <TokenHandler>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </TokenHandler>
    </div>
  );
}

export default App;
