import { Link, useLocation } from 'react-router-dom';
import { Briefcase, Users, Home, Upload, BarChart3 } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/candidates', label: 'Candidates', icon: Users },
  { to: '/upload', label: 'Upload', icon: Upload },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="bg-white border-b border-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 no-underline">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-text">
              Match<span className="text-primary">Engine</span>
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
              const isActive = pathname === to || (to !== '/' && pathname.startsWith(to));
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium no-underline transition-colors ${
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-secondary hover:text-text hover:bg-bg'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
