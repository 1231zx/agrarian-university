# fix_titles.py
import re
from pages_data_fixed import PAGES

# Словарь правильных названий для страниц без заголовка
TITLES_FIX = {
    'academic_council': 'Ученый совет',
    'additional_education': 'Дополнительное профессиональное образование',
    'admission_addresses': 'Адреса приема документов',
    'admission_committee': 'Приемная комиссия',
    'admission_docs': 'Документы для поступления',
    'admission_faq': 'Вопросы и ответы',
    'admission_info': 'Информация для поступающего',
    'admission_info_detail': 'Целевое обучение',
    'admission_regulations': 'Нормативные документы',
    'agro_classes': 'Агроклассы',
    'alumni': 'Выпускникам',
    'applicant_lists': 'Списки лиц, подавших документы',
    'applicant_main': 'Поступающему',
    'attestation': 'Государственная научная аттестация',
    'bonuses': 'Индивидуальные достижения',
    'candidate_exams': 'Кандидатские экзамены',
    'career_guidance': 'Профориентационная работа',
    'competition_lists': 'Конкурсные списки',
    'conferences': 'Научные конференции',
    'contacts_departments': 'Контакты подразделений',
    'cossack': 'Казачья сотня',
    'disabled_info': 'Информация для лиц с ОВЗ',
    'dissertations': 'Диссертационные работы',
    'doctoral': 'Докторантура',
    'dormitory': 'Общежитие',
    'educational_activity': 'Образовательная деятельность',
    'employee': 'Сотруднику',
    'employer': 'Работодателю',
    'endowment': 'Эндаумент фонд',
    'enrollment_info': 'Сведения о зачислении',
    'entrance_tests': 'Вступительные испытания',
    'exam_schedule': 'Расписание экзаменов',
    'grants': 'Гранты и конкурсы',
    'inclusive_education': 'Инклюзивное образование',
    'institute_agro': 'Институт агроэкологических технологий',
    'institute_biotech': 'Институт прикладной биотехнологии и ветеринарной медицины',
    'institute_economy': 'Институт экономики и управления АПК',
    'institute_engineering': 'Институт инженерных систем и энергетики',
    'institute_food': 'Институт пищевых производств',
    'institute_land': 'Институт землеустройства, кадастров и природообустройства',
    'institute_law': 'Юридический институт',
    'institute_achinsk': 'Ачинский филиал',
    'international': 'Международное сотрудничество',
    'international_students': 'Ассоциация иностранных студентов',
    'jalinga': 'Видеостудия Jalinga',
    'laboratories': 'Инновационные лаборатории',
    'leadership': 'Руководство университета',
    'library': 'Научная библиотека',
    'olympiads': 'Олимпиады и конкурсы',
    'paid_education': 'Платное обучение',
    'payment': 'Оплата обучения',
    'postgraduate': 'Аспирантура',
    'preparatory_courses': 'Подготовительные курсы',
    'professionalitet': 'Проект "Профессионалитет"',
    'psychologist': 'Психолог',
    'school_awards': 'Награды и достижения',
    'school_conferences': 'Конференции для школьников',
    'school_info': 'Школьнику',
    'school_news': 'Новости для школьников',
    'science': 'Научная деятельность',
    'science_news': 'Новости науки',
    'science_schools': 'Научные школы',
    'science_supervisors': 'Научные руководители',
    'social_support': 'Социальная защита',
    'sports_life': 'Спортивная жизнь',
    'structure': 'Структура университета',
    'student_calendar': 'Календарный график',
    'student_council': 'Студенческий совет',
    'student_educational_resources': 'Образовательные ресурсы',
    'student_faq': 'Часто задаваемые вопросы',
    'student_main': 'Студенту',
    'student_mass_courses': 'Зачёт массовых онлайн-курсов',
    'student_practice_bases': 'Базы практик',
    'student_practice_dates': 'Сроки практик',
    'student_practice_docs': 'Документы по практике',
    'student_practice_instruction': 'Инструктаж перед практикой',
    'student_practice_requests': 'Заявки от работодателей',
    'student_practice_survey': 'Анкета по практике',
    'student_projects': 'Проектная деятельность',
    'student_regulations': 'Нормативные документы',
    'student_scholarships': 'Стипендии',
    'student_survey': 'Анкетирование',
    'student_teams': 'Студенческие отряды',
    'student_textbooks': 'Учебные пособия',
    'target_education': 'Целевое обучение',
    'university_anticorruption': 'Противодействие коррупции',
    'university_main': 'Университет',
    'university_parent_council': 'Совет родителей',
    'university_popechitelskiy': 'Попечительский совет',
    'university_press': 'Наша пресса',
    'university_press_center': 'Пресс-центр',
    'university_today': 'Университет сегодня',
    'university_vesti': 'Журнал «Вести Красноярского ГАУ»',
    'university_vesti_archive': 'Архив журнала',
    'volunteer': 'Волонтерский центр',
}

# Создаём новый файл с исправленными названиями
with open('pages_data_fixed.py', 'w', encoding='utf-8') as f:
    f.write("# Автоматически сгенерированный файл со всеми страницами (ИСПРАВЛЕННЫЙ)\n")
    f.write("PAGES = {\n")
    
    for slug, data in PAGES.items():
        # Исправляем заголовок, если есть в словаре
        if slug in TITLES_FIX:
            title = TITLES_FIX[slug]
        else:
            title = data['title']
        
        f.write(f"    '{slug}': {{\n")
        f.write(f"        'title': '{title}',\n")
        f.write(f"        'template': '{data['template']}',\n")
        f.write(f"        'parent': {repr(data.get('parent', None))},\n")
        
        # Экранируем контент
        content = data['content'].replace("'''", "\\'\\'\\'")
        f.write(f"        'content': '''{content}''',\n")
        f.write(f"    }},\n")
    
    f.write("}\n")

print("✅ Исправленный файл создан: pages_data_fixed.py")
print(f"📊 Исправлено заголовков: {len(TITLES_FIX)}")