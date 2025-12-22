import { Routes, Route } from "react-router-dom";

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route
          path="/"
          element={
            <div className="flex items-center justify-center min-h-screen">
              <div className="text-center">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">
                  PR Review
                </h1>
                <p className="text-gray-600">
                  GitHub Pull Request monitoring application
                </p>
              </div>
            </div>
          }
        />
      </Routes>
    </div>
  );
}

export default App;
