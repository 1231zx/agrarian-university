import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Page

app = create_app()

# Полный список кафедр и их файлов
DEPARTMENTS = {
    # Институт агроэкологических технологий
    'institute_agro_department_agronomy': 'Кафедра общего земледелия и защиты растений',
    'institute_agro_department_plant_breeding': 'Кафедра растениеводства, селекции и семеноводства',
    'institute_agro_department_soil': 'Кафедра почвоведения и агрохимии',
    'institute_agro_department_landscape': 'Кафедра ландшафтной архитектуры и ботаники',
    'institute_agro_department_ecology': 'Кафедра экологии и природопользования',
    'institute_agro_department_physical_culture': 'Кафедра физической культуры',
    'institute_agro_department_languages': 'Кафедра иностранных языков и профессиональных коммуникаций',
    
    # Институт биотехнологии
    'institute_biotech_department_anatomy': 'Кафедра анатомии, патологической анатомии и хирургии',
    'institute_biotech_department_zootechny': 'Кафедра зоотехнии и технологии переработки',
    'institute_biotech_department_breeding': 'Кафедра разведения, генетики, биологии и водных биоресурсов',
    'institute_biotech_department_internal_diseases': 'Кафедра внутренних незаразных болезней, акушерства и физиологии',
    'institute_biotech_department_epizootology': 'Кафедра эпизоотологии, микробиологии, паразитологии',
    
    # Институт экономики
    'institute_economy_department_organization': 'Кафедра организации и экономики сельскохозяйственного производства',
    'institute_economy_department_management': 'Кафедра управления социально-экономическими системами',
    'institute_economy_department_information': 'Кафедра информационных технологий',
    'institute_economy_department_accounting': 'Кафедра бухгалтерского учета и статистики',
    'institute_economy_department_psychology': 'Кафедра психологии, педагогики и экологии человека',
    
    # Инженерный институт
    'institute_engineering_department_physics': 'Кафедра физики и математики',
    'institute_engineering_department_mechanization': 'Кафедра механизации и технического сервиса в АПК',
    'institute_engineering_department_general_engineering': 'Кафедра общеинженерных дисциплин',
    'institute_engineering_department_system_energy': 'Кафедра системоэнергетики',
    'institute_engineering_department_electrical_engineering': 'Кафедра теоретических основ электротехники',
    'institute_engineering_department_tractors': 'Кафедра тракторы и автомобили',
    'institute_engineering_department_electrical_supply': 'Кафедра электроснабжения сельского хозяйства',
    
    # Институт пищевых производств
    'institute_food_department_bakery': 'Кафедра технологии хлебопекарного, кондитерского и макаронного производств',
    'institute_food_department_canning': 'Кафедра технологии консервирования и пищевой биотехнологии',
    'institute_food_department_equipment': 'Кафедра технологии, оборудования бродильных и пищевых производств',
    'institute_food_department_quality': 'Кафедра товароведения и управления качеством продукции АПК',
    'institute_food_department_chemistry': 'Кафедра химии',
    
    # Институт землеустройства
    'institute_land_department_land_management': 'Кафедра землеустройства и кадастры',
    'institute_land_department_gis': 'Кафедра кадастра застроенных территорий и геоинформационных технологий',
    'institute_land_department_environmental': 'Кафедра природообустройства',
    'institute_land_department_safety': 'Кафедра безопасности жизнедеятельности',
    
    # Юридический институт
    'institute_law_department_theory': 'Кафедра теории и истории государства и права',
    'institute_law_department_civil': 'Кафедра гражданского права и процесса',
    'institute_law_department_criminal_procedure': 'Кафедра уголовного процесса, криминалистики',
    'institute_law_department_criminal_law': 'Кафедра уголовного права и криминологии',
    'institute_law_department_land_law': 'Кафедра земельного права и экологических экспертиз',
    'institute_law_department_history': 'Кафедра истории и политологии',
    'institute_law_department_philosophy': 'Кафедра философии',
    'institute_law_department_forensic': 'Кафедра судебных экспертиз',
    
    # Ачинский филиал
    'institute_achinsk_department_law': 'Кафедра правовых и социально-экономических дисциплин',
    'institute_achinsk_department_engineering': 'Кафедра агроинженерии',
}

def extract_full_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'{% block content %}(.*?){% endblock %}'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            body = match.group(1).strip()
            # Удаляем section page-header
            body = re.sub(r'<section class="page-header">.*?</section>', '', body, flags=re.DOTALL)
            return body
        return content
    except Exception as e:
        print(f'Ошибка: {e}')
        return ''

def force_update():
    with app.app_context():
        templates_dir = 'templates'
        updated = 0
        
        for slug, title in DEPARTMENTS.items():
            filepath = os.path.join(templates_dir, f'{slug}.html')
            
            if not os.path.exists(filepath):
                print(f'❌ Файл не найден: {slug}.html')
                continue
            
            content = extract_full_content(filepath)
            
            if not content:
                print(f'⚠️ Пустой контент: {slug}')
                continue
            
            page = Page.query.filter_by(slug=slug).first()
            if page:
                page.content = content
                page.title = title
                db.session.commit()
                updated += 1
                print(f'✅ Обновлена: {title}')
            else:
                print(f'❌ Страница не найдена: {slug}')
        
        print(f'\n🎉 Обновлено: {updated}')

if __name__ == '__main__':
    force_update()