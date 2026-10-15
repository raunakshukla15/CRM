import { Link } from 'react-router-dom';
import { btnPrimary, inputCls } from '../components/ui.jsx';

export function AuthShell({ title, subtitle, children }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2 mb-6">
          <span className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-lg">
            K
          </span>
          <span className="font-bold text-xl text-indigo-700">KilloKart</span>
        </div>
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
          <h1 className="text-xl font-bold">{title}</h1>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
          <div className="mt-4">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function AuthFooter({ to, label, text }) {
  return (
    <p className="text-sm text-gray-500 mt-4 text-center">
      {text}{' '}
      <Link to={to} className="text-indigo-600 hover:underline font-medium">
        {label}
      </Link>
    </p>
  );
}

export { btnPrimary, inputCls };
