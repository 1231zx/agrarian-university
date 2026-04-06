import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Page

app = create_app()

def extract_full_content_from_html(filepath):
    """Извлекает ПОЛНЫЙ контент из HTML файла кафедры"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Извлекаем блок content
        pattern = r'{% block content %}(.*?){% endblock %}'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            body = match.group(1).strip()
            # НЕ удаляем заголовок, он нужен
            return body
        return content
    except Exception as e:
        print(f'❌ Ошибка чтения {filepath}: {e}')
        return ''

def update_departments():
    with app.app_context():
        templates_dir = 'templates'
        updated = 0
        
        # Список кафедр для обновления
        department_slugs = [
            'institute_agro_department_agronomy',
            'institute_agro_department_plant_breeding', 
            'institute_agro_department_soil',
            'institute_agro_department_landscape',
            'institute_agro_department_ecology',
            'institute_agro_department_physical_culture',
            'institute_agro_department_languages',
            'institute_biotech_department_anatomy',
            'institute_biotech_department_zootechny',
            'institute_biotech_department_breeding',
            'institute_biotech_department_internal_diseases',
            'institute_biotech_department_epizootology',
            'institute_economy_department_organization',
            'institute_economy_department_management',
            'institute_economy_department_information',
            'institute_economy_department_accounting',
            'institute_economy_department_psychology',
            'institute_engineering_department_physics',
            'institute_engineering_department_mechanization',
            'institute_engineering_department_general_engineering',
            'institute_engineering_department_system_energy',
            'institute_engineering_department_electrical_engineering',
            'institute_engineering_department_tractors',
            'institute_engineering_department_electrical_supply',
            'institute_food_department_bakery',
            'institute_food_department_canning',
            'institute_food_department_equipment',
            'institute_food_department_quality',
            'institute_food_department_chemistry',
            'institute_land_department_land_management',
            'institute_land_department_gis',
            'institute_land_department_environmental',
            'institute_land_department_safety',
            'institute_law_department_theory',
            'institute_law_department_civil',
            'institute_law_department_criminal_procedure',
            'institute_law_department_criminal_law',
            'institute_law_department_land_law',
            'institute_law_department_history',
            'institute_law_department_philosophy',
            'institute_law_department_forensic',
            'institute_achinsk_department_law',
            'institute_achinsk_department_engineering',
        ]
        
        for slug in department_slugs:
            filepath = os.path.join(templates_dir, f'{slug}.html')
            
            if not os.path.exists(filepath):
                print(f'⚠️ Файл не найден: {slug}.html')
                continue
            
            full_content = extract_full_content_from_html(filepath)
            
            if not full_content:
                print(f'⚠️ Пустой контент: {slug}')
                continue
            
            # Находим страницу в БД
            page = Page.query.filter_by(slug=slug).first()
            if page:
                page.content = full_content
                db.session.commit()
                updated += 1
                print(f'✅ Обновлена: {page.title}')
            else:
                print(f'❌ Страница не найдена в БД: {slug}')
        
        print(f'\n🎉 Обновлено кафедр: {updated}')

if __name__ == '__main__':
    update_departments()