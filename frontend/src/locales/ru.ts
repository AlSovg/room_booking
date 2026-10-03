// Формы множественного числа: «один | несколько | много» (правило ruPlural в i18n.ts)
export default {
  app: { title: "Бронирование переговорных", name: "Переговорные" },
  lang: { switch: "Сменить язык" },
  nav: { calendar: "Календарь", rooms: "Комнаты", search: "Поиск", my: "Мои брони", main: "Основная навигация", sections: "Разделы" },
  user: {
    menu: "Меню пользователя", role: "Роль: {role}", admin: "Администратор", employee: "Сотрудник",
    adminPanel: "Администрирование", stats: "Статистика", logout: "Выйти",
  },
  login: {
    title: "Вход", subtitle: "Рабочая почта и пароль", password: "Пароль", hide: "Скрыть пароль", show: "Показать пароль",
    submit: "Войти", note: "Нет доступа — напишите администратору",
  },
  common: {
    from: "от", people: "человек", minCapacity: "Минимальная вместимость", room: "Комната", upTo: "до {n}",
    loading: "Загрузка…", noRooms: "Нет комнат под выбранные условия", close: "Закрыть", cancel: "Отмена",
    save: "Сохранить", add: "Добавить", edit: "Изменить", delete: "Удалить", status: "Статус", actions: "Действия",
  },
  cal: {
    upToShort: "до {n} чел.", prevDay: "Предыдущий день", nextDay: "Следующий день", today: "Сегодня",
    mine: "Мои", others: "Чужие", past: "Прошло", hint: "нажмите на свободное время, чтобы забронировать",
    newBooking: "Новая бронь",
  },
  rooms: {
    found: "найдено {n} из {total}", busyUntil: "Занята до", freeUntil: "Свободна до", freeAllDay: "Свободна до конца дня",
    schedule: "Расписание", capacity: "Вместимость", active: "Активна", inactive: "Неактивна",
    editAria: "Изменить комнату {name}", note: "Комнаты не удаляются — неактивная скрыта из поиска и календаря, история броней сохраняется.",
    edit: "Изменить комнату", new: "Новая комната", location: "Местоположение", description: "Описание",
    activeHint: "Неактивную комнату нельзя забронировать",
  },
  room: {
    capacityAria: "Вместимость до {n} человек", all: "Все комнаты", upToPeople: "до {n} человек", book: "Забронировать",
    prevWeek: "Предыдущая неделя", nextWeek: "Следующая неделя", hint: "Выделите время в сетке, чтобы забронировать",
    goToDate: "Перейти к дате", weekday: "День недели",
  },
  booking: {
    edit: "Изменить бронь", taken: "Это время уже занято", showInCalendar: "Показать в календаре", date: "Дата",
    start: "Начало", end: "Конец", topic: "Тема", topicPh: "Например, ревью дизайна", attendees: "Участников",
    outOf: "из {n}", book: "Забронировать",
  },
  search: {
    title: "Поиск свободной комнаты", from: "С", to: "До", find: "Найти", equipment: "Нужно оборудование",
    none: "Свободных комнат нет", yourSlot: "Ваш интервал", busy: "Занято", dayBusyAria: "Занятость {name} на день", free: "Свободна",
  },
  my: {
    cancelTitle: "Отменить бронь?", cancelText: "«{title}» будет отменена, комната освободится.", cancelConfirm: "Отменить бронь",
    roomN: "Комната №{id}", period: "Период", none: "Нет броней", soon: "через {n} мин", cancelAria: "Отменить бронь «{title}»",
    scope: { upcoming: "Предстоящие", past: "Прошедшие", cancelled: "Отменённые" },
  },
  notif: {
    ariaUnread: "Уведомления, {n} непрочитанных", title: "Уведомления", new: "{n} новых", readAll: "Прочитать все",
    none: "Уведомлений нет", unread: "Не прочитано",
    kind: { reminder: "Скоро начнётся", changed: "Бронь изменена", cancelled: "Бронь отменена" },
  },
  admin: { equipment: "Оборудование", users: "Пользователи", addRoom: "Добавить комнату", sections: "Разделы администрирования" },
  equip: {
    renameTitle: "Переименовать оборудование", deleteTitle: "Удалить оборудование?", deleteText: "«{name}» будет удалено.",
    unused: "не используется", renameAria: "Переименовать {name}", deleteAria: "Удалить {name}", new: "Новое оборудование",
    name: "Название", namePh: "Например, Флипчарт",
  },
  users: {
    resetTitle: "Сбросить пароль?", resetText: "Для {email} будет создан новый временный пароль, старый перестанет работать.",
    resetConfirm: "Сбросить", fullName: "ФИО", fullNamePh: "Фамилия Имя", role: "Роль", create: "Создать",
    tempPassword: "Временный пароль для {email} — показан один раз", copy: "Скопировать", hide: "Скрыть", user: "Пользователь",
    active: "Активен", blocked: "Заблокирован", you: "это вы", makeEmployee: "Сделать сотрудником",
    makeAdmin: "Сделать администратором", resetAria: "Сбросить пароль {email}", blockAria: "Заблокировать {name}",
    unblockAria: "Разблокировать {name}",
  },
  stats: {
    d7: "7 дней", d30: "30 дней", d90: "Квартал", min: "мин", h: "ч", from: "С", to: "По",
    summaryFor: "Сводка за {from} – {to}", csv: "Скачать CSV: {what}", summary: "сводка", bookings: "Броней",
    forDays: "за {days}", cancelled: "Отменено", ofAll: "от всех броней", avgDuration: "Средняя длительность",
    ofCompleted: "по состоявшимся", booked: "Забронировано", sumRooms: "сумма по комнатам", utilization: "Загрузка комнат",
    peak: "Пиковые часы", less: "меньше", more: "больше", total: "Всего", activeCol: "Активных", hours: "Часов",
    cancelRate: "Доля отмен",
  },
  time: {
    justNow: "только что", minAgo: "{n} мин назад", today: "сегодня", yesterday: "вчера",
    todayCap: "Сегодня", tomorrow: "Завтра", yesterdayCap: "Вчера",
  },
  errors: { request: "Не удалось выполнить запрос" },
  plural: {
    freeRooms: "Свободна {n} комната | Свободны {n} комнаты | Свободны {n} комнат",
    fromPeople: "от {n} человека | от {n} человек | от {n} человек",
    attendees: "{n} участник | {n} участника | {n} участников",
    inRooms: "в {n} комнате | в {n} комнатах | в {n} комнатах",
    bookings: "{n} бронь | {n} брони | {n} броней",
    days: "{n} день | {n} дня | {n} дней",
  },
};
