import React from 'react';
import { NavLink, useNavigate } from 'react-router';
import { Search, ArrowRight, LayoutGrid, FileText, Home as HomeIcon, Wallet, Users, Briefcase, Heart, Car, Building2, CircleAlert, Clock, Calendar, Bell } from 'lucide-react';
import { categories, popularProblems, notifications, mockUser } from '../mockData';
import { Button, Card, Input, Badge } from '../components/ui';

const iconMap = {
  LayoutGrid, FileText, Home: HomeIcon, Wallet, Users, Briefcase, Heart, Car, Building2
};

export const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col gap-8 md:gap-[48px]">
      {/* Mobile Top Bar (Greeting) */}
      <div className="md:hidden flex items-center justify-between mt-2 mb-4">
        <div>
          <h2 className="text-2xl font-bold">Привет, {mockUser.name.split(' ')[0]}! 👋</h2>
          <p className="text-gray-500 text-sm mt-1">Чем можем помочь сегодня?</p>
        </div>
        <NavLink to="/notifications" className="relative p-2 text-gray-500 hover:bg-gray-100 rounded-full transition-colors">
          <Bell className="w-6 h-6" />
          <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span>
        </NavLink>
      </div>

      {/* Hero Section */}
      <section className="text-left md:text-center max-w-3xl md:mx-auto space-y-4 md:space-y-6">
        <h1 className="hidden md:block text-4xl md:text-5xl font-bold tracking-tight text-gray-900">
          Помощь в решении жизненных ситуаций
        </h1>
        <p className="hidden md:block text-lg text-gray-600">
          Сервис поможет понять, что делать, куда обращаться и какие документы нужны в любой ситуации.
        </p>
        <div className="pt-2 md:pt-4 flex flex-col sm:flex-row gap-3 max-w-2xl md:mx-auto">
          <Input 
            icon={<Search className="w-5 h-5" />} 
            placeholder="Опишите проблему..." 
            className="text-base md:text-lg h-12 md:h-14 w-full rounded-2xl"
          />
          <Button onClick={() => navigate('/catalog')} className="hidden sm:flex px-8 shrink-0 h-14 rounded-2xl">
            Найти
          </Button>
        </div>
      </section>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 md:gap-6">
        {/* Left Column (Content) */}
        <div className="lg:col-span-8 space-y-10 md:space-y-12">
          
          {/* Quick Categories */}
          <section>
            <h2 className="text-xl md:text-2xl font-bold mb-4 md:mb-6">Категории</h2>
            <div className="grid grid-cols-2 min-[400px]:grid-cols-3 sm:grid-cols-4 gap-3 md:gap-4">
              {categories.slice(1, 9).map(cat => {
                const Icon = iconMap[cat.icon as keyof typeof iconMap];
                return (
                  <NavLink key={cat.id} to={`/catalog?category=${cat.id}`} className="block group">
                    <Card className="p-3 md:p-6 flex flex-col items-center justify-center text-center gap-2 md:gap-3 hover:border-emerald-500 hover:shadow-md transition-all cursor-pointer h-full rounded-2xl">
                      <div className="w-12 h-12 md:w-12 md:h-12 rounded-full bg-gray-50 flex items-center justify-center text-gray-600 group-hover:bg-emerald-50 group-hover:text-emerald-600 transition-colors">
                        {Icon && <Icon className="w-6 h-6 md:w-6 md:h-6" />}
                      </div>
                      <span className="font-medium text-xs md:text-sm text-gray-900 leading-tight">{cat.name}</span>
                    </Card>
                  </NavLink>
                );
              })}
            </div>
          </section>

          {/* Popular Problems */}
          <section>
            <div className="flex items-center justify-between mb-4 md:mb-6">
              <h2 className="text-xl md:text-2xl font-bold">Популярные проблемы</h2>
              <NavLink to="/catalog" className="hidden sm:flex text-emerald-600 hover:text-emerald-700 font-medium text-sm items-center gap-1">
                Смотреть все <ArrowRight className="w-4 h-4" />
              </NavLink>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
              {popularProblems.map(problem => (
                <NavLink key={problem.id} to={`/problem/${problem.id}`}>
                  <Card className="p-4 md:p-5 hover:border-emerald-500 transition-colors cursor-pointer group h-full flex flex-col rounded-2xl">
                    <h3 className="font-semibold text-base md:text-lg mb-1 md:mb-2 group-hover:text-emerald-600 transition-colors">{problem.title}</h3>
                    <p className="text-gray-500 text-sm flex-grow line-clamp-2">{problem.desc}</p>
                  </Card>
                </NavLink>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4 sm:hidden h-12 rounded-xl" onClick={() => navigate('/catalog')}>
              Смотреть все проблемы
            </Button>
          </section>

        </div>

        {/* Right Column (Sidebar/Important) */}
        <div className="lg:col-span-4">
          <Card className="p-5 md:p-6 sticky top-28 bg-blue-50/50 border-blue-100 rounded-2xl md:rounded-[20px]">
            <h3 className="text-lg md:text-xl font-bold mb-4 md:mb-6 flex items-center gap-2">
              <CircleAlert className="w-5 h-5 text-blue-600" />
              Напоминания
            </h3>
            <div className="space-y-3 md:space-y-4">
              {notifications.slice(0,3).map(notif => (
                <div key={notif.id} className="bg-white p-3 md:p-4 rounded-xl border border-gray-100 shadow-sm">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 md:mt-1 flex-shrink-0">
                      {notif.type === 'document' && <Clock className="w-4 h-4 md:w-5 md:h-5 text-orange-500" />}
                      {notif.type === 'task' && <Calendar className="w-4 h-4 md:w-5 md:h-5 text-blue-500" />}
                      {notif.type === 'law' && <FileText className="w-4 h-4 md:w-5 md:h-5 text-emerald-500" />}
                    </div>
                    <div>
                      <h4 className="font-medium text-sm mb-1 leading-tight">{notif.title}</h4>
                      <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{notif.desc}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4 md:mt-6 bg-white h-12 rounded-xl md:rounded-2xl" onClick={() => navigate('/notifications')}>
              Все напоминания
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
};