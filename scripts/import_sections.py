import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Page

app = create_app()

# Разделы и их подстраницы
SECTIONS = [
    # Главные страницы разделов
    {'slug': 'student_main', 'title': 'Студенту', 'template': 'student_section', 'parent': None},
    {'slug': 'applicant_main', 'title': 'Поступающему', 'template': 'applicant_section', 'parent': None},
    {'slug': 'university_main', 'title': 'Университет', 'template': 'university_section', 'parent': None},
    {'slug': 'science', 'title': 'Наука и инновации', 'template': 'science_section', 'parent': None},
    
    # Подразделы Студенту
    {'slug': 'student_council', 'title': 'Объединённый совет обучающихся', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_teams', 'title': 'Студенческие отряды', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'cultural_center', 'title': 'Культурно-досуговый центр', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'sports_life', 'title': 'Спортивная жизнь', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'psychologist', 'title': 'Психолог', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'social_support', 'title': 'Социальная защита', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_projects', 'title': 'Проектная деятельность', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_faq', 'title': 'Часто задаваемые вопросы', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_calendar', 'title': 'Календарный график', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_scholarships', 'title': 'Стипендии и меры поддержки', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_regulations', 'title': 'Нормативные документы', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_educational_resources', 'title': 'Образовательные ресурсы', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_mass_courses', 'title': 'Массовые онлайн-курсы', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_textbooks', 'title': 'Учебные пособия', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_practice_bases', 'title': 'Базы практик', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_practice_dates', 'title': 'Сроки проведения практик', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_practice_docs', 'title': 'Документы по практике', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_practice_instruction', 'title': 'Инструктаж перед практикой', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_practice_requests', 'title': 'Заявки от работодателей', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_practice_survey', 'title': 'Анкета удовлетворённости практикой', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'student_survey', 'title': 'Анкетирование обучающихся', 'template': 'info_page', 'parent': 'student_main'},
    {'slug': 'international_students', 'title': 'Ассоциация иностранных студентов', 'template': 'info_page', 'parent': 'student_main'},
    
    # Подразделы Поступающему
    {'slug': 'admission_info', 'title': 'Информация для поступающего', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'admission_committee', 'title': 'Приемная комиссия', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'admission_docs', 'title': 'Документы для поступления', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'admission_faq', 'title': 'Вопросы и ответы', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'admission_addresses', 'title': 'Адреса приема документов', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'entrance_tests', 'title': 'Вступительные испытания', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'competition_lists', 'title': 'Конкурсные списки', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'applicant_lists', 'title': 'Списки подавших документы', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'enrollment_orders', 'title': 'Приказы о зачислении', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'target_education', 'title': 'Целевое обучение', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'paid_education', 'title': 'Платное обучение', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'bonuses', 'title': 'Индивидуальные достижения', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'disabled_info', 'title': 'Информация для лиц с ОВЗ', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'postgraduate_admission', 'title': 'Поступление в аспирантуру', 'template': 'info_page', 'parent': 'applicant_main'},
    {'slug': 'doctoral_admission', 'title': 'Поступление в докторантуру', 'template': 'info_page', 'parent': 'applicant_main'},
    
    # Подразделы Университет
    {'slug': 'university_today', 'title': 'Университет сегодня', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'university_history', 'title': 'История', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'university_association', 'title': 'Ассоциация выпускников', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'university_profsoyuz', 'title': 'Профсоюзная организация', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'university_press', 'title': 'Наша пресса', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'university_press_center', 'title': 'Пресс-центр', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'media_about_us', 'title': 'СМИ о нас', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'university_brandbook', 'title': 'Брендбук', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'university_vesti', 'title': 'Вести университета', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'quality_management', 'title': 'Система менеджмента качества', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'endowment', 'title': 'Эндаумент фонд', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'driving_school', 'title': 'Автошкола', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'jalinga', 'title': 'Видеостудия Jalinga', 'template': 'info_page', 'parent': 'university_main'},
    {'slug': 'prosecutor_explains', 'title': 'Прокурор разъясняет', 'template': 'info_page', 'parent': 'university_main'},
]

def extract_content_from_html(filepath):
    """Извлекает контент из HTML файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'{% block content %}(.*?){% endblock %}'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            body = match.group(1).strip()
            body = re.sub(r'<section class="page-header">.*?</section>', '', body, flags=re.DOTALL)
            return body.strip()
        return content
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return ''

def import_sections():
    with app.app_context():
        templates_dir = 'templates'
        imported = 0
        skipped = 0
        
        # Сначала создаем все страницы
        for section in SECTIONS:
            slug = section['slug']
            filepath = os.path.join(templates_dir, f'{slug}.html')
            
            if not os.path.exists(filepath):
                print(f'⚠️ Файл не найден: {slug}.html')
                skipped += 1
                continue
            
            content = extract_content_from_html(filepath)
            
            if not content:
                print(f'⚠️ Пустой контент: {slug}')
                skipped += 1
                continue
            
            existing = Page.query.filter_by(slug=slug).first()
            if existing:
                print(f'⏭️ Уже существует: {slug}')
                skipped += 1
                continue
            
            page = Page(
                slug=slug,
                title=section['title'],
                content=content,
                template=section['template'],
                published=True
            )
            db.session.add(page)
            imported += 1
            print(f'✅ Импортирован: {section["title"]}')
        
        db.session.commit()
        
        # Теперь устанавливаем parent_id
        for section in SECTIONS:
            if section['parent']:
                child = Page.query.filter_by(slug=section['slug']).first()
                parent = Page.query.filter_by(slug=section['parent']).first()
                if child and parent:
                    child.parent_id = parent.id
                    db.session.commit()
                    print(f'🔗 Привязан: {section["title"]} → {parent.title}')
        
        print(f'\n🎉 Импорт завершен! Импортировано: {imported}, Пропущено: {skipped}')

if __name__ == '__main__':
    import_sections()