import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router';
import { ArrowLeft, CircleCheckBig, Circle, Clock, FileText, Calendar as CalendarIcon, Pen } from 'lucide-react';
import { childbirthTasks } from '../mockData';
import { Card, Badge, Progress, Button, Checkbox } from '../components/ui';

export const SituationDetails = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState(childbirthTasks);
  const [activeTab, setActiveTab] = useState('tasks');

  const toggleTask = (id: number) => {
    setTasks(tasks.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
  };

  const progress = Math.round((tasks.filter(t => t.completed).length / tasks.length) * 100);

  return (
    <div className="space-y-6 md:space-y-8 flex flex-col min-h-full pb-20 md:pb-0">
      {/* Mobile Top Bar */}
      <div className="md:hidden flex items-center gap-3 mb-2 sticky top-0 bg-[#F8FAFC] z-10 py-3 -mx-4 px-4">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-xl font-bold truncate">Рождение ребёнка</h1>
      </div>

      <div className="hidden md:block">
        <NavLink to="/situations" className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 mb-4 text-sm font-medium transition-colors">
          <ArrowLeft className="w-4 h-4" /> Назад к ситуациям
        </NavLink>
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-3xl font-bold">Рождение ребёнка</h1>
          <Badge variant="blue" className="text-sm px-4 py-1.5">В процессе</Badge>
        </div>
      </div>

      <Card className="p-5 md:p-6 rounded-2xl border-gray-100 shadow-sm">
        <div className="flex justify-between items-center text-sm mb-3">
          <span className="font-medium text-gray-700">Общий прогресс</span>
          <span className="font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">{progress}%</span>
        </div>
        <Progress value={progress} className="h-2 md:h-3" />
      </Card>

      {/* Segmented Control / Tabs */}
      <div className="flex overflow-x-auto hide-scrollbar gap-1 md:gap-2 border-b border-gray-200 -mx-4 px-4 md:mx-0 md:px-0">
        {[
          { id: 'tasks', label: 'Задачи' },
          { id: 'docs', label: 'Документы' },
          { id: 'time', label: 'Сроки' },
          { id: 'notes', label: 'Заметки' }
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

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'tasks' && (
          <div className="space-y-3">
            {tasks.map(task => (
              <div 
                key={task.id} 
                className={`flex items-start gap-3 p-4 rounded-2xl border border-gray-100 transition-all ${task.completed ? 'bg-gray-50/50 opacity-75' : 'bg-white shadow-sm hover:border-emerald-300'}`}
              >
                <Checkbox 
                  id={`task-${task.id}`}
                  checked={task.completed}
                  onCheckedChange={() => toggleTask(task.id)}
                  className="mt-0.5 w-5 h-5 md:w-6 md:h-6 rounded-md data-[state=checked]:bg-emerald-500 data-[state=checked]:border-emerald-500" 
                />
                <label htmlFor={`task-${task.id}`} className="flex-grow cursor-pointer select-none">
                  <span className={`block font-medium text-sm md:text-base leading-tight ${task.completed ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                    {task.title}
                  </span>
                  <span className="text-xs text-gray-500 flex items-center gap-1 mt-2">
                    <Clock className="w-3.5 h-3.5" /> {task.deadline}
                  </span>
                </label>
              </div>
            ))}
            <Button variant="outline" className="w-full mt-4 border border-dashed border-gray-300 text-gray-500 h-12 rounded-2xl bg-white hover:bg-gray-50">
              <Plus className="w-4 h-4 mr-2" /> Добавить свою задачу
            </Button>
          </div>
        )}

        {activeTab === 'docs' && (
          <div className="text-center py-12 px-4 text-gray-500 border-2 border-dashed border-gray-200 rounded-2xl bg-white">
            <FileText className="w-12 h-12 mx-auto text-gray-300 mb-3" />
            <p className="text-sm md:text-base">Здесь будут храниться загруженные документы.</p>
            <Button variant="outline" className="mt-6 rounded-xl h-12 px-6">Загрузить документ</Button>
          </div>
        )}

        {activeTab === 'time' && (
          <div className="text-center py-12 px-4 text-gray-500 border-2 border-dashed border-gray-200 rounded-2xl bg-white">
             <CalendarIcon className="w-12 h-12 mx-auto text-gray-300 mb-3" />
             <p className="text-sm md:text-base">Календарь событий и дедлайнов.</p>
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="text-center py-12 px-4 text-gray-500 border-2 border-dashed border-gray-200 rounded-2xl bg-white">
             <Pen className="w-12 h-12 mx-auto text-gray-300 mb-3" />
             <p className="text-sm md:text-base">Ваши личные заметки по ситуации.</p>
          </div>
        )}
      </div>
    </div>
  );
};