import { Navigate, Route, Routes } from 'react-router-dom';
import Shell from './components/layout.jsx';
import { Loader } from './components/ui.jsx';
import { AuthProvider, useAuth } from './lib/auth.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Customers from './pages/Customers.jsx';
import CustomerDetail from './pages/CustomerDetail.jsx';
import Orders from './pages/Orders.jsx';
import Communications from './pages/Communications.jsx';
import FollowUps from './pages/FollowUps.jsx';
import Activity from './pages/Activity.jsx';
import Integrations from './pages/Integrations.jsx';
import Settings from './pages/Settings.jsx';
import SignIn from './pages/SignIn.jsx';
import SignUp from './pages/SignUp.jsx';
import ForgotPassword from './pages/ForgotPassword.jsx';
import ResetPassword from './pages/ResetPassword.jsx';

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Loader label="Restoring session…" />;
  if (!user) return <Navigate to="/signin" replace />;
  return <Shell>{children}</Shell>;
}

function PublicOnly({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Loader label="Loading…" />;
  if (user) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/signin" element={<PublicOnly><SignIn /></PublicOnly>} />
        <Route path="/signup" element={<PublicOnly><SignUp /></PublicOnly>} />
        <Route path="/forgot-password" element={<PublicOnly><ForgotPassword /></PublicOnly>} />
        <Route path="/reset-password" element={<PublicOnly><ResetPassword /></PublicOnly>} />
        <Route path="/" element={<Protected><Dashboard /></Protected>} />
        <Route path="/customers" element={<Protected><Customers /></Protected>} />
        <Route path="/customers/:id" element={<Protected><CustomerDetail /></Protected>} />
        <Route path="/orders" element={<Protected><Orders /></Protected>} />
        <Route path="/communications" element={<Protected><Communications /></Protected>} />
        <Route path="/followups" element={<Protected><FollowUps /></Protected>} />
        <Route path="/activity" element={<Protected><Activity /></Protected>} />
        <Route path="/integrations" element={<Protected><Integrations /></Protected>} />
        <Route path="/settings" element={<Protected><Settings /></Protected>} />
        <Route path="*" element={<Protected><Dashboard /></Protected>} />
      </Routes>
    </AuthProvider>
  );
}
