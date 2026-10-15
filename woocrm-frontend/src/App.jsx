import { Route, Routes } from 'react-router-dom';
import Shell from './components/layout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Customers from './pages/Customers.jsx';
import CustomerDetail from './pages/CustomerDetail.jsx';
import Orders from './pages/Orders.jsx';
import FollowUps from './pages/FollowUps.jsx';
import Integrations from './pages/Integrations.jsx';

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/customers/:id" element={<CustomerDetail />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/followups" element={<FollowUps />} />
        <Route path="/integrations" element={<Integrations />} />
      </Routes>
    </Shell>
  );
}
