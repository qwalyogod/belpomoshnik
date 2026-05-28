import React, { useState } from 'react';
import { Users, FileText, Activity, TriangleAlert, Plus, Search, Pencil, Trash2, EyeOff, CheckCircle } from 'lucide-react';
import { popularProblems } from '../mockData';
import { Card, Button, Input, Badge } from '../components/ui';

export const Admin = () => {
  const [activeTab, setActiveTab] = useState('problems');

  const stats = [
    { label: 'Пользователи', value: '12,450', icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Проблемы в базе', value: '142', icon: TriangleAlert, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: 'Создано планов', value: '8,210', icon: Activity, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Закон-апдейты', value: '45', icon: FileText, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  return (
    <div className="space-y-6 md:space-y-8 flex flex-col min-h-full pb-20 md:pb-0">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl md:text-3xl font-bold">Админ-панель</h1>
        <div className="hidden md:flex gap-3">
          <Button className="gap-2">
            <Plus className="w-4 h-4" /> Добавить проблему
          </Button>
          <Button variant="outline" className="gap-2">
            <Plus className="w-4 h-4" /> Добавить закон
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-6">
        {stats.map((stat, idx) => (
          <Card key={idx} className="p-4 md:p-6 rounded-2xl">
            <div className={`w-10 h-10 md:w-12 md:h-12 rounded-xl flex items-center justify-center mb-3 md:mb-4 ${stat.bg} ${stat.color}`}>
              <stat.icon className="w-5 h-5 md:w-6 md:h-6" />
            </div>
            <div className="text-xl md:text-3xl font-bold mb-1">{stat.value}</div>
            <div className="text-[10px] md:text-sm text-gray-500 font-medium">{stat.label}</div>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex overflow-x-auto hide-scrollbar gap-1 md:gap-2 border-b border-gray-200 -mx-4 px-4 md:mx-0 md:px-0">
        {[
          { id: 'problems', label: 'Проблемы' },
          { id: 'laws', label: 'Законы' },
          { id: 'users', label: 'Пользователи' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`whitespace-nowrap px-4 md:px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'problems' && (
        <div className="space-y-4 md:space-y-6">
          <div className="flex justify-between items-center gap-4 bg-white p-2 rounded-2xl md:bg-transparent md:p-0">
            <div className="max-w-md w-full">
              <Input icon={<Search className="w-4 h-4" />} placeholder="Поиск проблем..." className="h-10 md:h-12 rounded-xl" />
            </div>
            <Badge variant="blue" className="hidden sm:inline-flex">Всего: {popularProblems.length}</Badge>
          </div>

          {/* Desktop Table View */}
          <Card className="hidden md:block overflow-hidden rounded-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-gray-50 text-gray-500 text-sm">
                  <tr>
                    <th className="px-6 py-4 font-medium">ID</th>
                    <th className="px-6 py-4 font-medium">Название</th>
                    <th className="px-6 py-4 font-medium">Категория</th>
                    <th className="px-6 py-4 font-medium">Статус</th>
                    <th className="px-6 py-4 font-medium text-right">Действия</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {popularProblems.map((prob) => (
                    <tr key={prob.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-6 py-4 text-sm font-mono text-gray-500">{prob.id}</td>
                      <td className="px-6 py-4 font-medium">{prob.title}</td>
                      <td className="px-6 py-4">
                        <Badge>{prob.category}</Badge>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="success">Опубликовано</Badge>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex justify-end gap-2">
                          <button className="p-2 text-gray-400 hover:text-blue-600 transition-colors rounded-lg hover:bg-blue-50">
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-gray-400 hover:text-red-600 transition-colors rounded-lg hover:bg-red-50">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Mobile Card View */}
          <div className="md:hidden space-y-3">
            {popularProblems.map((prob) => (
              <Card key={prob.id} className="p-4 rounded-2xl flex flex-col gap-3">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs font-mono text-gray-400 mb-1 block">#{prob.id}</span>
                    <h3 className="font-bold text-gray-900 leading-tight">{prob.title}</h3>
                  </div>
                  <Badge variant="success" className="text-[10px] px-2 py-0.5">Опубликовано</Badge>
                </div>
                
                <div className="flex items-center justify-between mt-2">
                  <Badge className="text-[10px] bg-gray-100 text-gray-600">{prob.category}</Badge>
                  <div className="flex gap-1">
                    <button className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button className="p-2 bg-gray-50 text-gray-600 rounded-lg">
                      <EyeOff className="w-4 h-4" />
                    </button>
                    <button className="p-2 bg-red-50 text-red-600 rounded-lg">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Forms placeholders for Admin */}
          <Card className="p-5 md:p-8 border-dashed border-2 border-gray-200 mt-8 rounded-2xl bg-gray-50/50">
            <h3 className="text-lg font-bold mb-4">Быстрое создание проблемы</h3>
            <div className="grid md:grid-cols-2 gap-4 md:gap-6 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Название</label>
                <Input placeholder="Например: Восстановление ВУ" className="bg-white rounded-xl" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Категория</label>
                <select className="w-full h-12 bg-white border border-gray-200 rounded-xl px-4 text-gray-900 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors">
                  <option>Авто</option>
                  <option>Документы</option>
                  <option>Здоров��е</option>
                </select>
              </div>
              <div className="md:col-span-2">
                 <label className="block text-sm font-medium text-gray-700 mb-2">Шаги плана (по одному на строку)</label>
                 <textarea className="w-full h-32 bg-white border border-gray-200 rounded-xl p-4 text-gray-900 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors resize-none" placeholder="1. Написать заявление...&#10;2. Оплатить пошлину..."></textarea>
              </div>
            </div>
            <Button className="w-full md:w-auto h-12 rounded-xl px-8">Создать черновик</Button>
          </Card>
        </div>
      )}

      {/* Mobile Fixed Floating Action Button for Admin */}
      <div className="md:hidden fixed bottom-[80px] right-4 z-40">
        <button className="w-14 h-14 bg-gray-900 text-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-800 active:scale-95 transition-all">
          <Plus className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
};