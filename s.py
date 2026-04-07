from app import create_app
from models import db, Page

app = create_app()
with app.app_context():
    # Проверяем институты
    institutes = Page.query.filter_by(template='institute').all()
    print(f"Институтов в БД: {len(institutes)}")
    for inst in institutes:
        print(f"  - {inst.title} (slug: {inst.slug})")
    
    # Проверяем кафедры
    departments = Page.query.filter_by(template='department').all()
    print(f"\nКафедр в БД: {len(departments)}")
    for dept in departments:
        parent_name = dept.parent.title if dept.parent else "Нет родителя"
        print(f"  - {dept.title} -> относится к: {parent_name}")