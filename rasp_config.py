# Файл с настройками отображения расписания
# Здесь можно задать понятные названия для файлов

SCHEDULE_CONFIG = {
    # PDF файлы
    'class schedule 1st year 2nd semester full-time study.pdf': {
        'title': '1 курс (2 семестр)',
        'description': 'Расписание занятий для 1 курса, очная форма',
        'institute': 'Все институты'
    },
    'class schedule 2nd year 4th semester full-time study.pdf': {
        'title': '2 курс (4 семестр)',
        'description': 'Расписание занятий для 2 курса, очная форма',
        'institute': 'Все институты'
    },
    'Introductory instructions.pdf': {
        'title': 'Вступительные испытания - инструкция',
        'description': 'Инструкция для поступающих, правила проведения экзаменов',
        'institute': 'Абитуриентам'
    },
    'Schedule of consultations for undergraduate programs and exams.pdf': {
        'title': 'Консультации для бакалавров',
        'description': 'Расписание консультаций по программам бакалавриата',
        'institute': 'Бакалавриат'
    },
    'Schedule of consultations on Master\'s degree programs.pdf': {
        'title': 'Консультации для магистров',
        'description': 'Расписание консультаций по программам магистратуры',
        'institute': 'Магистратура'
    },
    'Schedule of entrance examinations for Master\'s degree programs.pdf': {
        'title': 'Вступительные экзамены - магистратура',
        'description': 'Расписание вступительных испытаний в магистратуру',
        'institute': 'Абитуриентам'
    },
    'Schedule of entrance exams for bachelor\'s and specialist programs.pdf.pdf': {
        'title': 'Вступительные экзамены - бакалавриат и специалитет',
        'description': 'Расписание вступительных испытаний',
        'institute': 'Абитуриентам'
    },
    
    # Excel файлы ЦПССЗ
    'CPSSZ2.xls': {
        'title': 'ЦПССЗ - все курсы',
        'description': 'Расписание для Центра подготовки специалистов среднего звена (1-4 курсы)',
        'institute': 'ЦПССЗ'
    },
    
    # Excel файлы ИАЭТ
    'IAT2.xls': {
        'title': 'ИАЭТ - все курсы',
        'description': 'Институт агроэкологических технологий (1-4 курсы)',
        'institute': 'ИАЭТ'
    },
    
    # Excel файлы ИЭиУ АПК
    'IEU2.xls': {
        'title': 'ИЭиУ АПК - все курсы',
        'description': 'Институт экономики и управления АПК (1-4 курсы)',
        'institute': 'ИЭиУ АПК'
    },
    'IEUv2.xls': {
        'title': 'ИЭиУ АПК - вечернее отделение',
        'description': 'Институт экономики и управления АПК, вечерняя форма',
        'institute': 'ИЭиУ АПК'
    },
    
    # Другие институты
    'IiSiE2.xlsx': {
        'title': 'ИИСиЭ - расписание',
        'description': 'Институт информационных систем и инженерии',
        'institute': 'ИИСиЭ'
    },
    'IPBVM2.xls': {
        'title': 'ИПБиВМ - все курсы',
        'description': 'Институт прикладной биотехнологии и ветеринарной медицины',
        'institute': 'ИПБиВМ'
    },
    'IPP2.xls': {
        'title': 'ИПП - все курсы',
        'description': 'Институт пищевых производств',
        'institute': 'ИПП'
    },
    'IZKP2.xls': {
        'title': 'ИЗКиП - все курсы',
        'description': 'Институт землеустройства, кадастров и природообустройства',
        'institute': 'ИЗКиП'
    },
    'UI2.xlsx': {
        'title': 'Юридический институт - расписание',
        'description': 'Юридический институт',
        'institute': 'ЮИ'
    },
    'UIv2.xlsx': {
        'title': 'Юридический институт - вечернее отделение',
        'description': 'Юридический институт, вечерняя форма',
        'institute': 'ЮИ'
    }
}

# Группировка по институтам для удобной навигации
INSTITUTES = {
    'Все институты': [],
    'Абитуриентам': [],
    'ЦПССЗ': [],
    'ИАЭТ': [],
    'ИЭиУ АПК': [],
    'ИИСиЭ': [],
    'ИПБиВМ': [],
    'ИПП': [],
    'ИЗКиП': [],
    'ЮИ': [],
    'Бакалавриат': [],
    'Магистратура': []
}