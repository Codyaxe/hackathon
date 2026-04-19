import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { type ReactNode } from 'react';

import Dashboard from './pages/Dashboard';
import DataInput from './pages/DataInput';
import Reports from './pages/Reports';
import ResponseLibrary from './pages/ResponseLibrary';
import Settings from './pages/Settings';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const isAuth = localStorage.getItem('esg_auth');
  return isAuth === 'true' ? <>{children}</> : <Navigate to="/login" replace />;
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/data-input" element={
          <ProtectedRoute>
            <DataInput />
          </ProtectedRoute>
        } />
        <Route path="/reports" element={
          <ProtectedRoute>
            <Reports />
          </ProtectedRoute>
        } />
        <Route path="/response-library" element={
          <ProtectedRoute>
            <ResponseLibrary />
          </ProtectedRoute>
        } />
        <Route path="/settings" element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}
