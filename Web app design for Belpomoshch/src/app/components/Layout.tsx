import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router';
import { Bell, Home, Search, ListTodo, User } from 'lucide-react';
import { mockUser } from '../mockData';

export const Layout = () => {
  const location = useLocation();

  const navLinks = [
    { to: "/", label: "Главная" },
    { to: "/catalog", label: "Проблемы" },
    { to: "/situations", label: "Мои ситуации" },
    { to: "/documents", label: "Документы" },
    { to: "/laws", label: "Законы" },
  ];

  const mobileNavLinks = [
    { to: "/", label: "Главная", icon: Home },
    { to: "/catalog", label: "Проблемы", icon: Search },
    { to: "/situations", label: "Ситуации", icon: ListTodo },
    { to: "/notifications", label: "Уведомления", icon: Bell },
    { to: "/profile", label: "Профиль", icon: User },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] font-sans text-gray-900 flex flex-col">
      {/* Header - Desktop Only */}
      <header className="hidden md:flex sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-[1440px] w-full mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-12">
            <NavLink to="/" className="flex items-center gap-2 text-emerald-600">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-xl">
                Б
              </div>
              <span className="font-bold text-xl tracking-tight">Белпомощник</span>
            </NavLink>
            
            <nav className="flex items-center gap-1">
              {navLinks.map(link => (
                <NavLink 
                  key={link.to} 
                  to={link.to}
                  className={({isActive}) => `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}`}
                >
                  {link.label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <NavLink to="/notifications" className="relative p-2 text-gray-500 hover:text-gray-700 transition-colors rounded-full hover:bg-gray-100">
              <Bell className="w-6 h-6" />
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span>
            </NavLink>
            <div className="w-px h-8 bg-gray-200 mx-2"></div>
            <NavLink to="/profile" className="flex items-center gap-3 group">
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900 group-hover:text-emerald-600 transition-colors">{mockUser.name}</div>
                <div className="text-xs text-gray-500">Профиль</div>
              </div>
              <img src={mockUser.avatarUrl} alt="Avatar" className="w-10 h-10 rounded-full object-cover border border-gray-200" />
            </NavLink>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="flex-grow w-full max-w-[1200px] mx-auto px-4 md:px-6 py-4 md:py-12 pb-24 md:pb-12">
        <Outlet />
      </main>
      
      {/* Simple Footer - Desktop Only */}
      <footer className="hidden md:block bg-white border-t border-gray-100 py-8 mt-auto">
        <div className="max-w-[1200px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between text-gray-500 text-sm">
          <div>© 2026 Белпомощник. Информационная система для граждан РБ.</div>
          <div className="flex gap-4 mt-4 md:mt-0">
            <NavLink to="/admin" className="hover:text-emerald-600">Админ-панель</NavLink>
            <a href="#" className="hover:text-emerald-600">О проекте</a>
          </div>
        </div>
      </footer>

      {/* Bottom Navigation - Mobile Only */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 flex justify-around items-center pt-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))] px-2">
        {mobileNavLinks.map(link => {
          const isActive = location.pathname === link.to || (link.to !== '/' && location.pathname.startsWith(link.to));
          return (
            <NavLink 
              key={link.to} 
              to={link.to}
              className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${isActive ? 'text-emerald-600' : 'text-gray-500'}`}
            >
              <link.icon className={`w-6 h-6 ${isActive ? 'fill-emerald-50 text-emerald-600' : ''}`} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-[10px] font-medium">{link.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
};
