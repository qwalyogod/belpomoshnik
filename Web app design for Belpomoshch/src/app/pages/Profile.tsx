import React from 'react';
import { Camera, Mail, MapPin, Tag, Settings, Bell, ChevronRight, LogOut, CircleHelp } from 'lucide-react';
import { mockUser } from '../mockData';
import { Card, Button, Input, Badge } from '../components/ui';

export const Profile = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6 md:space-y-8 flex flex-col min-h-full pb-20 md:pb-0">
      <h1 className="text-2xl md:text-3xl font-bold">Профиль</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
        <div className="md:col-span-1 space-y-6">
          <Card className="p-6 text-center flex flex-col items-center rounded-2xl">
            <div className="relative mb-4">
              <img 
                src={mockUser.avatarUrl} 
                alt={mockUser.name} 
                className="w-24 h-24 md:w-32 md:h-32 rounded-full object-cover border-4 border-white shadow-lg"
              />
              <button className="absolute bottom-0 right-0 w-8 h-8 md:w-10 md:h-10 bg-emerald-600 text-white rounded-full flex items-center justify-center hover:bg-emerald-700 transition-colors border-2 border-white shadow-sm">
                <Camera className="w-4 h-4 md:w-5 md:h-5" />
              </button>
            </div>
            <h2 className="text-xl md:text-2xl font-bold">{mockUser.name}</h2>
            <p className="text-gray-500 mb-2 flex items-center gap-1.5 justify-center mt-1 text-sm md:text-base">
              <MapPin className="w-4 h-4" /> {mockUser.city}, {mockUser.region}
            </p>
          </Card>

          {/* Mobile Menu Links */}
          <div className="md:hidden space-y-2">
            {[
              { icon: Settings, label: "Личные данные" },
              { icon: Tag, label: "Мои интересы" },
              { icon: Bell, label: "Уведомления" },
              { icon: CircleHelp, label: "Помощь и поддержка" },
            ].map((item, i) => (
              <button key={i} className="w-full bg-white p-4 rounded-2xl border border-gray-100 flex items-center justify-between active:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center text-gray-600">
                    <item.icon className="w-5 h-5" />
                  </div>
                  <span className="font-medium">{item.label}</span>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </button>
            ))}
          </div>

          <Card className="hidden md:block p-6 rounded-2xl">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Tag className="w-5 h-5 text-emerald-600" /> Мои интересы
            </h3>
            <div className="flex flex-wrap gap-2">
              {mockUser.interests.map((interest, idx) => (
                <Badge key={idx} className="bg-emerald-50 text-emerald-700 hover:bg-emerald-100 cursor-pointer transition-colors">
                  {interest}
                </Badge>
              ))}
              <Badge className="bg-gray-50 text-gray-500 border border-dashed border-gray-300 cursor-pointer hover:bg-gray-100 transition-colors">
                + Добавить
              </Badge>
            </div>
            <p className="text-xs text-gray-400 mt-4 leading-relaxed">
              Интересы помогают нам подбирать для вас актуальные новости и законы.
            </p>
          </Card>
        </div>

        <div className="md:col-span-2 space-y-6">
          <Card className="hidden md:block p-8 rounded-2xl">
            <h3 className="text-xl font-bold mb-6">Личные данные</h3>
            <div className="space-y-5">
              <div className="grid sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Имя и фамилия</label>
                  <Input defaultValue={mockUser.name} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <Input defaultValue={mockUser.email} icon={<Mail className="w-4 h-4" />} />
                </div>
              </div>
              <div className="grid sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Регион</label>
                  <Input defaultValue={mockUser.region} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Город / Населенный пункт</label>
                  <Input defaultValue={mockUser.city} />
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-5 md:p-8 rounded-2xl border-gray-100">
            <h3 className="text-lg md:text-xl font-bold mb-4 md:mb-6 flex items-center gap-2">
              <Settings className="w-5 h-5 text-gray-500 hidden md:block" /> Настройки системы
            </h3>
            
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="pr-4">
                  <div className="font-medium text-gray-900 text-sm md:text-base">Крупный шрифт</div>
                  <div className="text-xs md:text-sm text-gray-500">Увеличить размер текста</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer shrink-0">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div className="pr-4">
                  <div className="font-medium text-gray-900 text-sm md:text-base">Высокий контраст</div>
                  <div className="text-xs md:text-sm text-gray-500">Повышенная контрастность</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer shrink-0">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                </label>
              </div>

              <div className="w-full h-px bg-gray-100"></div>

              <div className="flex items-center justify-between">
                <div className="flex gap-3 pr-4">
                  <Bell className="w-5 h-5 text-emerald-600 mt-0.5 hidden md:block" />
                  <div>
                    <div className="font-medium text-gray-900 text-sm md:text-base">Email-уведомления</div>
                    <div className="text-xs md:text-sm text-gray-500">Оповещения на почту</div>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer shrink-0">
                  <input type="checkbox" defaultChecked className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                </label>
              </div>
            </div>
          </Card>

          <div className="hidden md:flex justify-end pt-4">
            <Button size="lg" className="w-full sm:w-auto px-12 h-12 rounded-xl">
              Сохранить изменения
            </Button>
          </div>

          <div className="md:hidden mt-4">
            <button className="w-full bg-white p-4 rounded-2xl border border-red-100 flex items-center justify-center gap-2 text-red-600 font-medium active:bg-red-50 transition-colors">
              <LogOut className="w-5 h-5" />
              Выйти из аккаунта
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};