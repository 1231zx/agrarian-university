import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Page

app = create_app()

# Соответствие кафедр и институтов (slug кафедры → slug института)
DEPARTMENT_PARENTS = {
    # Институт агроэкологических технологий (уже есть)
    'institute_agro_department_agronomy': 'institute_agro',
    'institute_agro_department_plant_breeding': 'institute_agro',
    'institute_agro_department_soil': 'institute_agro',
    'institute_agro_department_landscape': 'institute_agro',
    'institute_agro_department_ecology': 'institute_agro',
    'institute_agro_department_physical_culture': 'institute_agro',
    'institute_agro_department_languages': 'institute_agro',
    
    # Институт биотехнологии
    'institute_biotech_department_anatomy': 'institute_biotech',
    'institute_biotech_department_zootechny': 'institute_biotech',
    'institute_biotech_department_breeding': 'institute_biotech',
    'institute_biotech_department_internal_diseases': 'institute_biotech',
    'institute_biotech_department_epizootology': 'institute_biotech',
    
    # Институт экономики
    'institute_economy_department_organization': 'institute_economy',
    'institute_economy_department_management': 'institute_economy',
    'institute_economy_department_information': 'institute_economy',
    'institute_economy_department_accounting': 'institute_economy',
    'institute_economy_department_psychology': 'institute_economy',
    
    # Инженерный институт
    'institute_engineering_department_physics': 'institute_engineering',
    'institute_engineering_department_mechanization': 'institute_engineering',
    'institute_engineering_department_general_engineering': 'institute_engineering',
    'institute_engineering_department_system_energy': 'institute_engineering',
    'institute_engineering_department_electrical_engineering': 'institute_engineering',
    'institute_engineering_department_tractors': 'institute_engineering',
    'institute_engineering_department_electrical_supply': 'institute_engineering',
    
    # Институт пищевых производств
    'institute_food_department_bakery': 'institute_food',
    'institute_food_department_canning': 'institute_food',
    'institute_food_department_equipment': 'institute_food',
    'institute_food_department_quality': 'institute_food',
    'institute_food_department_chemistry': 'institute_food',
    
    # Институт землеустройства
    'institute_land_department_land_management': 'institute_land',
    'institute_land_department_gis': 'institute_land',
    'institute_land_department_environmental': 'institute_land',
    'institute_land_department_safety': 'institute_land',
    
    # Юридический институт
    'institute_law_department_theory': 'institute_law',
    'institute_law_department_civil': 'institute_law',
    'institute_law_department_criminal_procedure': 'institute_law',
    'institute_law_department_criminal_law': 'institute_law',
    'institute_law_department_land_law': 'institute_law',
    'institute_law_department_history': 'institute_law',
    'institute_law_department_philosophy': 'institute_law',
    'institute_law_department_forensic': 'institute_law',
    
    # Ачинский филиал
    'institute_achinsk_department_law': 'institute_achinsk',
    'institute_achinsk_department_engineering': 'institute_achinsk',
}

def extract_title_and_content(filepath):
    """Извлекает заголовок и контент из HTML файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Извлекаем заголовок из <h1> или из блока title
        title_match = re.search(r'<title>(.*?) - ООО Аграрный Университет</title>', content)
        if not title_match:
            title_match = re.search(r'<h1>(.*?)</h1>', content)
        
        title = title_match.group(1).strip() if title_match else ''
        
        # Извлекаем основной контент
        content_match = re.search(r'{% block content %}(.*?){% endblock %}', content, re.DOTALL)
        if content_match:
            body = content_match.group(1).strip()
            # Убираем заголовок из контента (чтобы не дублировался)
            body = re.sub(r'<section class="page-header">.*?</section>', '', body, flags=re.DOTALL)
            body = body.strip()
        else:
            body = content
        
        return title, body
    except Exception as e:
        print(f'❌ Ошибка чтения {filepath}: {e}')
        return '', ''

def import_departments():
    with app.app_context():
        templates_dir = 'templates'
        imported = 0
        skipped = 0
        
        for slug, parent_slug in DEPARTMENT_PARENTS.items():
            filepath = os.path.join(templates_dir, f'{slug}.html')
            
            if not os.path.exists(filepath):
                print(f'⚠️ Файл не найден: {slug}.html')
                skipped += 1
                continue
            
            # Получаем родительскую страницу
            parent = Page.query.filter_by(slug=parent_slug).first()
            if not parent:
                print(f'⚠️ Родитель не найден: {parent_slug} для {slug}')
                skipped += 1
                continue
            
            title, content = extract_title_and_content(filepath)
            
            if not title:
                title = slug.replace('_', ' ').title()
            
            # Проверяем, существует ли уже
            existing = Page.query.filter_by(slug=slug).first()
            if existing:
                print(f'⏭️ Уже существует: {slug}')
                skipped += 1
                continue
            
            page = Page(
                slug=slug,
                title=title,
                content=content,
                template='department',
                parent_id=parent.id,
                meta_description=f'Кафедра {title} Красноярского ГАУ',
                published=True
            )
            db.session.add(page)
            imported += 1
            print(f'✅ Импортирована кафедра: {title}')
        
        db.session.commit()
        print(f'\n🎉 Импорт завершен! Импортировано: {imported}, Пропущено: {skipped}')

if __name__ == '__main__':
    import_departments()