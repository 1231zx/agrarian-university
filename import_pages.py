# scripts/import_pages.py
import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Page

app = create_app()

# Данные для каждой страницы (slug, template, parent)
PAGES_DATA = {
    # ИНСТИТУТЫ (родительские страницы)
    'institute_agro': {
        'title': 'Институт агроэкологических технологий',
        'template': 'institute',
        'meta_description': 'Подготовка специалистов в области растениеводства, агрохимии, экологии и природопользования'
    },
    'institute_biotech': {
        'title': 'Институт прикладной биотехнологии и ветеринарной медицины',
        'template': 'institute',
        'meta_description': 'Подготовка ветеринарных врачей, биотехнологов и зоотехников'
    },
    'institute_economy': {
        'title': 'Институт экономики и управления АПК',
        'template': 'institute',
        'meta_description': 'Подготовка экономистов, менеджеров и управленцев для АПК'
    },
    'institute_engineering': {
        'title': 'Институт инженерных систем и энергетики',
        'template': 'institute',
        'meta_description': 'Подготовка инженеров для сельского хозяйства'
    },
    'institute_food': {
        'title': 'Институт пищевых производств',
        'template': 'institute',
        'meta_description': 'Подготовка технологов пищевой промышленности'
    },
    'institute_land': {
        'title': 'Институт землеустройства, кадастров и природообустройства',
        'template': 'institute',
        'meta_description': 'Подготовка землеустроителей, кадастровых инженеров'
    },
    'institute_law': {
        'title': 'Юридический институт',
        'template': 'institute',
        'meta_description': 'Подготовка юристов и судебных экспертов'
    },
    'institute_achinsk': {
        'title': 'Ачинский филиал',
        'template': 'institute',
        'meta_description': 'Филиал в г. Ачинск'
    },
    
    # ОСТАЛЬНЫЕ 170+ СТРАНИЦ ДОБАВИМ ПОТОМ...
}

def extract_content_from_html(filepath):
    """Извлекает контент из HTML файла (между {% block content %} и {% endblock %})"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем блок content
        pattern = r'{% block content %}(.*?){% endblock %}'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        return content
    except Exception as e:
        print(f'❌ Ошибка чтения {filepath}: {e}')
        return ''

def import_pages():
    with app.app_context():
        templates_dir = 'templates'
        
        for slug, data in PAGES_DATA.items():
            filepath = os.path.join(templates_dir, f'{slug}.html')
            
            if os.path.exists(filepath):
                content = extract_content_from_html(filepath)
                
                page = Page.query.filter_by(slug=slug).first()
                if not page:
                    page = Page(slug=slug)
                
                page.title = data['title']
                page.content = content
                page.template = data['template']
                page.meta_description = data.get('meta_description', '')
                page.published = True
                
                db.session.add(page)
                print(f'✅ Импортирован: {slug}')
            else:
                print(f'⚠️ Файл не найден: {filepath}')
        
        db.session.commit()
        print('\n🎉 Импорт завершен!')

if __name__ == '__main__':
    import_pages()