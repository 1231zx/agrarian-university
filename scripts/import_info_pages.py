import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Page

app = create_app()

# Список информационных страниц
INFO_PAGES = [
    {'slug': 'about', 'title': 'О нас', 'template': 'info_page'},
    {'slug': 'contacts', 'title': 'Контакты', 'template': 'info_page'},
    {'slug': 'library', 'title': 'Научная библиотека', 'template': 'info_page'},
    {'slug': 'structure', 'title': 'Структура университета', 'template': 'info_page'},
    {'slug': 'leadership', 'title': 'Руководство', 'template': 'info_page'},
    {'slug': 'academic_council', 'title': 'Ученый совет', 'template': 'info_page'},
    {'slug': 'departments', 'title': 'Управления и отделы', 'template': 'info_page'},
    {'slug': 'educational_activity', 'title': 'Образовательная деятельность', 'template': 'info_page'},
    {'slug': 'science', 'title': 'Научная деятельность', 'template': 'info_page'},
    {'slug': 'laboratories', 'title': 'Инновационные лаборатории', 'template': 'info_page'},
    {'slug': 'grants', 'title': 'Гранты и конкурсы', 'template': 'info_page'},
    {'slug': 'conferences', 'title': 'Конференции', 'template': 'info_page'},
    {'slug': 'international', 'title': 'Международное сотрудничество', 'template': 'info_page'},
    {'slug': 'dormitory', 'title': 'Общежитие', 'template': 'info_page'},
    {'slug': 'payment', 'title': 'Оплата обучения', 'template': 'info_page'},
    {'slug': 'volunteer', 'title': 'Волонтерский центр', 'template': 'info_page'},
    {'slug': 'cossack', 'title': 'Казачья сотня', 'template': 'info_page'},
    {'slug': 'inclusive_education', 'title': 'Инклюзивное образование', 'template': 'info_page'},
    {'slug': 'additional_education', 'title': 'Дополнительное образование', 'template': 'info_page'},
    {'slug': 'professionalitet', 'title': 'Профессионалитет', 'template': 'info_page'},
    {'slug': 'school_info', 'title': 'Школьнику', 'template': 'info_page'},
    {'slug': 'olympiads', 'title': 'Олимпиады и конкурсы', 'template': 'info_page'},
    {'slug': 'preparatory_courses', 'title': 'Подготовительные курсы', 'template': 'info_page'},
    {'slug': 'career_guidance', 'title': 'Профориентационная работа', 'template': 'info_page'},
    {'slug': 'postgraduate', 'title': 'Аспирантура', 'template': 'info_page'},
    {'slug': 'doctoral', 'title': 'Докторантура', 'template': 'info_page'},
    {'slug': 'attestation', 'title': 'Аттестация', 'template': 'info_page'},
    {'slug': 'employee', 'title': 'Сотруднику', 'template': 'info_page'},
    {'slug': 'employer', 'title': 'Работодателю', 'template': 'info_page'},
    {'slug': 'alumni', 'title': 'Выпускнику', 'template': 'info_page'},
]

def extract_content_from_html(filepath):
    """Извлекает контент из HTML файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Извлекаем основной контент
        pattern = r'{% block content %}(.*?){% endblock %}'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            body = match.group(1).strip()
            # Убираем заголовок из контента
            body = re.sub(r'<section class="page-header">.*?</section>', '', body, flags=re.DOTALL)
            return body.strip()
        return content
    except Exception as e:
        print(f'❌ Ошибка чтения {filepath}: {e}')
        return ''

def import_info_pages():
    with app.app_context():
        templates_dir = 'templates'
        imported = 0
        skipped = 0
        
        for page_info in INFO_PAGES:
            slug = page_info['slug']
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
            
            # Проверяем, существует ли уже
            existing = Page.query.filter_by(slug=slug).first()
            if existing:
                print(f'⏭️ Уже существует: {slug}')
                skipped += 1
                continue
            
            page = Page(
                slug=slug,
                title=page_info['title'],
                content=content,
                template=page_info['template'],
                meta_description=f'{page_info["title"]} - Красноярский ГАУ',
                published=True
            )
            db.session.add(page)
            imported += 1
            print(f'✅ Импортирована: {page_info["title"]}')
        
        db.session.commit()
        print(f'\n🎉 Импорт завершен! Импортировано: {imported}, Пропущено: {skipped}')

if __name__ == '__main__':
    import_info_pages()