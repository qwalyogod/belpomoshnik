import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router';
import { CircleCheck, Circle, CircleAlert, FileText, MapPin, Clock, CreditCard, Download, Plus, Bookmark, ArrowLeft, ChevronDown } from 'lucide-react';
import { Card, Button, Badge, Accordion, AccordionItem, AccordionTrigger, AccordionContent, Checkbox } from '../components/ui';

export const ProblemDetails = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('now');
  
  const sections = [
    { id: 'now', label: 'Что делать' },
    { id: 'plan', label: 'Пошаговый план' },
    { id: 'docs', label: 'Документы' },
    { id: 'time', label: 'Сроки' },
    { id: 'cost', label: 'Стоимость' },
    { id: 'where', label: 'Куда обращаться' },
    { id: 'errors', label: 'Частые ошибки' },
    { id: 'templates', label: 'Шаблоны' },
  ];

  const steps = [
    "Написать заявление в милиции и получить справку",
    "Сделать 4 цветные фотографии (40х50 мм)",
    "Оплатить государственную пошлину",
    "Собрать остальные документы",
    "Подать документы в ОГиМ или РСЦ",
    "Забрать новый паспорт"
  ];

  return (
    <div className="flex flex-col min-h-[calc(100vh-theme(spacing.16))] pb-24">
      {/* Mobile Header */}
      <div className="md:hidden flex items-center gap-3 mb-4 sticky top-0 bg-[#F8FAFC] z-10 py-3 -mx-4 px-4">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-xl font-bold truncate">Потерял паспорт</h1>
        <button className="p-2 ml-auto text-gray-600 hover:bg-gray-100 rounded-full">
          <Bookmark className="w-5 h-5" />
        </button>
      </div>

      {/* Desktop Header */}
      <div className="hidden md:flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-8 mb-8">
        <div>
          <Badge className="mb-3">Документы</Badge>
          <h1 className="text-3xl font-bold">Потерял паспорт</h1>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="gap-2">
            <Bookmark className="w-4 h-4" /> Сохранить себе
          </Button>
          <Button className="gap-2">
            <Plus className="w-4 h-4" /> Создать персональный план
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative flex-grow">
        {/* Sidebar Navigation - Desktop Only */}
        <div className="hidden lg:block lg:col-span-3">
          <div className="sticky top-28 flex flex-col gap-1">
            {sections.map(section => (
              <button
                key={section.id}
                onClick={() => {
                  setActiveTab(section.id);
                  document.getElementById(section.id)?.scrollIntoView({ behavior: 'smooth' });
                }}
                className={`text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${activeTab === section.id ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                {section.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content - Desktop (Sections) & Mobile (Accordion) */}
        <div className="lg:col-span-9">
          
          {/* Mobile Accordion */}
          <div className="md:hidden bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <Accordion type="single" defaultValue="now" className="w-full">
              
              <AccordionItem value="now" className="border-b border-gray-100 px-4">
                <AccordionTrigger className="py-4 text-base font-bold hover:no-underline flex gap-2">
                  <span className="flex items-center gap-2"><CircleAlert className="w-5 h-5 text-orange-500" /> Что делать прямо сейчас</span>
                </AccordionTrigger>
                <AccordionContent className="pb-4">
                  <div className="p-4 bg-orange-50/50 border border-orange-100 rounded-xl">
                    <ul className="space-y-4">
                      <li className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center font-bold text-sm mt-0.5">1</span>
                        <span className="text-gray-800 text-sm leading-relaxed">Убедитесь, что паспорт действительно утерян, а не забыт дома.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center font-bold text-sm mt-0.5">2</span>
                        <span className="text-gray-800 text-sm leading-relaxed">Немедленно обратитесь в ближайшее отделение милиции (РУВД) для написания заявления.</span>
                      </li>
                    </ul>
                  </div>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="plan" className="border-b border-gray-100 px-4">
                <AccordionTrigger className="py-4 text-base font-bold hover:no-underline">Пошаговый план</AccordionTrigger>
                <AccordionContent className="pb-4 space-y-3">
                  {steps.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 rounded-xl border border-gray-100 hover:border-emerald-200 bg-white transition-colors">
                      <Checkbox id={`m-step-${idx}`} className="mt-0.5" />
                      <label htmlFor={`m-step-${idx}`} className="text-gray-700 text-sm leading-tight cursor-pointer select-none">{step}</label>
                    </div>
                  ))}
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="docs" className="border-b border-gray-100 px-4">
                <AccordionTrigger className="py-4 text-base font-bold hover:no-underline">Документы</AccordionTrigger>
                <AccordionContent className="pb-4">
                  <ul className="space-y-2 text-sm text-gray-600 list-disc list-inside px-2">
                    <li>Заявление (заполняется на месте)</li>
                    <li>4 цветные фотографии 40х50 мм</li>
                    <li>Свидетельство о рождении</li>
                    <li>Квитанция об оплате госпошлины</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="time" className="border-b border-gray-100 px-4">
                <AccordionTrigger className="py-4 text-base font-bold hover:no-underline">Сроки и Стоимость</AccordionTrigger>
                <AccordionContent className="pb-4 space-y-4">
                  <div>
                    <h4 className="font-semibold text-sm mb-2 text-gray-900">Сроки</h4>
                    <ul className="space-y-2 text-sm text-gray-600">
                      <li className="flex justify-between border-b border-gray-50 pb-1"><span>Стандартный</span><span className="font-medium">1 месяц</span></li>
                      <li className="flex justify-between border-b border-gray-50 pb-1"><span>Ускоренно</span><span className="font-medium">15 дней</span></li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm mb-2 text-gray-900">Стоимость</h4>
                    <ul className="space-y-2 text-sm text-gray-600">
                      <li className="flex justify-between border-b border-gray-50 pb-1"><span>Выдача</span><span className="font-medium">1 БВ (40 BYN)</span></li>
                      <li className="flex justify-between border-b border-gray-50 pb-1"><span>Ускорение</span><span className="font-medium">+ 1 БВ</span></li>
                    </ul>
                  </div>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="where" className="border-b border-gray-100 px-4">
                <AccordionTrigger className="py-4 text-base font-bold hover:no-underline">Куда обращаться</AccordionTrigger>
                <AccordionContent className="pb-4">
                  <p className="text-sm text-gray-600 mb-3">
                    В расчетно-справочный центр (РСЦ), товарищество собственников или ЖЭУ по месту регистрации.
                  </p>
                  <Button variant="outline" className="w-full text-sm h-10">Найти на карте</Button>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="templates" className="px-4">
                <AccordionTrigger className="py-4 text-base font-bold hover:no-underline">Шаблоны</AccordionTrigger>
                <AccordionContent className="pb-4">
                  <div className="p-3 border border-gray-100 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-gray-400" />
                      <div>
                        <div className="text-sm font-medium">Бланк заявления</div>
                        <div className="text-[10px] text-gray-500">PDF, 156 KB</div>
                      </div>
                    </div>
                    <button className="p-2 text-emerald-600 bg-emerald-50 rounded-lg">
                      <Download className="w-4 h-4" />
                    </button>
                  </div>
                </AccordionContent>
              </AccordionItem>

            </Accordion>
          </div>

          {/* Desktop Content Blocks */}
          <div className="hidden md:block space-y-12">
            <section id="now" className="scroll-mt-32">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <CircleAlert className="w-6 h-6 text-orange-500" />
                Что делать прямо сейчас
              </h2>
              <Card className="p-6 bg-orange-50/50 border-orange-100">
                <ul className="space-y-4">
                  <li className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center font-bold text-sm mt-0.5">1</span>
                    <span className="text-gray-800 leading-relaxed">Убедитесь, что паспорт действительно утерян, а не забыт дома.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center font-bold text-sm mt-0.5">2</span>
                    <span className="text-gray-800 leading-relaxed">Немедленно обратитесь в ближайшее отделение милиции (РУВД) для написания заявления об утере, чтобы вашим документом не воспользовались мошенники.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center font-bold text-sm mt-0.5">3</span>
                    <span className="text-gray-800 leading-relaxed">Возьмите в милиции талон-уведомление (он понадобится для восстановления).</span>
                  </li>
                </ul>
              </Card>
            </section>

            <section id="plan" className="scroll-mt-32">
              <h2 className="text-2xl font-bold mb-6">Пошаговый план</h2>
              <div className="space-y-4">
                {steps.map((step, idx) => (
                  <div key={idx} className="flex items-start gap-4 p-4 rounded-xl border border-gray-100 hover:border-emerald-200 bg-white transition-colors">
                    <Checkbox id={`d-step-${idx}`} className="mt-1" />
                    <label htmlFor={`d-step-${idx}`} className="text-gray-700 pt-0.5 cursor-pointer select-none">{step}</label>
                  </div>
                ))}
              </div>
            </section>
            
            <div className="grid md:grid-cols-2 gap-6">
              <section id="docs" className="scroll-mt-32">
                <Card className="p-6 h-full">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-500" />
                    Документы
                  </h2>
                  <ul className="space-y-3 text-sm text-gray-600 list-disc list-inside">
                    <li>Заявление (заполняется на месте)</li>
                    <li>4 цветные фотографии 40х50 мм (одним листом)</li>
                    <li>Свидетельство о рождении</li>
                    <li>Квитанция об оплате госпошлины</li>
                    <li>Талон-уведомление из милиции (при краже)</li>
                  </ul>
                </Card>
              </section>

              <section id="time" className="scroll-mt-32">
                <Card className="p-6 h-full">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-blue-500" />
                    Сроки
                  </h2>
                  <ul className="space-y-3 text-sm text-gray-600">
                    <li className="flex justify-between border-b border-gray-50 pb-2">
                      <span>Стандартный срок</span>
                      <span className="font-medium text-gray-900">1 месяц</span>
                    </li>
                    <li className="flex justify-between border-b border-gray-50 pb-2">
                      <span>Ускоренно</span>
                      <span className="font-medium text-gray-900">15 дней</span>
                    </li>
                  </ul>
                </Card>
              </section>
            </div>
            
          </div>
        </div>
      </div>

      {/* Mobile Fixed Bottom Action */}
      <div className="md:hidden fixed bottom-16 left-0 right-0 p-4 bg-white border-t border-gray-100 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-50">
        <Button className="w-full h-12 rounded-2xl text-base shadow-sm">
          Создать персональный план
        </Button>
      </div>
    </div>
  );
};