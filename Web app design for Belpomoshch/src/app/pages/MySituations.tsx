import React from 'react';
import { NavLink } from 'react-router';
import { Plus, Clock, CircleCheck, Circle } from 'lucide-react';
import { userSituations } from '../mockData';
import { Card, Button, Badge, Progress } from '../components/ui';

export const MySituations = () => {
  return (
    <div className="space-y-6 md:space-y-8 flex flex-col min-h-full pb-20 md:pb-0">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl md:text-3xl font-bold">Мои ситуации</h1>
        <Button className="hidden md:flex gap-2 h-12 rounded-2xl">
          <Plus className="w-5 h-5" /> Добавить ситуацию
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {userSituations.map(sit => {
          let statusBadge = "default";
          if (sit.status === "В процессе") statusBadge = "blue";
          if (sit.status === "Завершено") statusBadge = "success";
          
          return (
            <NavLink key={sit.id} to={`/situations/${sit.id}`}>
              <Card className="p-5 md:p-6 h-full flex flex-col hover:shadow-md transition-shadow group cursor-pointer border-gray-200 rounded-2xl">
                <div className="flex justify-between items-start mb-3 md:mb-4">
                  <Badge variant={statusBadge as any} className="text-[10px] md:text-xs px-2.5 py-1">{sit.status}</Badge>
                </div>
                
                <h3 className="text-lg md:text-xl font-bold mb-5 md:mb-6 group-hover:text-emerald-600 transition-colors leading-tight">
                  {sit.title}
                </h3>
                
                <div className="mt-auto space-y-2">
                  <div className="flex justify-between text-xs md:text-sm text-gray-500 font-medium">
                    <span>Прогресс</span>
                    <span>{sit.progress}%</span>
                  </div>
                  <Progress value={sit.progress} className="h-2 md:h-3" />
                </div>
              </Card>
            </NavLink>
          );
        })}
      </div>

      {/* Mobile Fixed Floating Action Button or Bottom Button */}
      <div className="md:hidden fixed bottom-[80px] right-4 z-40">
        <button className="w-14 h-14 bg-emerald-600 text-white rounded-full flex items-center justify-center shadow-lg hover:bg-emerald-700 active:scale-95 transition-all">
          <Plus className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
};