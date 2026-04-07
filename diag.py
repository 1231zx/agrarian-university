from app import create_app
from models import db, Page
import os

app = create_app()
with app.app_context():
    # 1. Проверяем существование страницы в БД
    page = Page.query.filter_by(slug='enrollment_orders').first()
    
    print("=" * 60)
    print("1️⃣ ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    if page:
        print(f"✅ Страница найдена:")
        print(f"   Slug: {page.slug}")
        print(f"   Title: {page.title}")
        print(f"   Published: {page.published}")
        print(f"   Template: {page.template}")
    else:
        print(f"❌ Страница с slug='enrollment_orders' НЕ найдена")
        print(f"   Возможно, вы создали с другим slug?")
        print(f"\n📋 Все страницы с 'enrollment' или 'order' в slug:")
        pages = Page.query.filter(
            db.or_(
                Page.slug.like('%enrollment%'),
                Page.slug.like('%order%')
            )
        ).all()
        for p in pages:
            print(f"   - {p.slug}: {p.title}")
        exit()

    # 2. Проверяем существование шаблона
    print("\n" + "=" * 60)
    print("2️⃣ ПРОВЕРКА ШАБЛОНА")
    print("=" * 60)
    
    possible_paths = [
        f"templates/dynamic/{page.template}.html",
        f"templates/{page.template}.html",
        f"templates/{page.slug}.html",
        f"templates/dynamic/{page.slug}.html"
    ]
    
    template_found = False
    for path in possible_paths:
        full_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full_path):
            print(f"✅ Шаблон найден: {path}")
            template_found = True
            break
        else:
            print(f"❌ Нет: {path}")
    
    if not template_found:
        print(f"\n⚠️ Шаблон НЕ НАЙДЕН! Нужно создать файл: templates/dynamic/{page.template}.html")
        print(f"   Или исправить template в БД на существующий (например, 'info_page')")
    
    # 3. Проверяем маршрут
    print("\n" + "=" * 60)
    print("3️⃣ ПРОВЕРКА МАРШРУТА В app.py")
    print("=" * 60)
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "@app.route('/new/<slug>')" in content:
        print("✅ Маршрут /new/<slug> существует")
    else:
        print("❌ Маршрут /new/<slug> НЕ НАЙДЕН!")
    
    # 4. Предлагаем исправление
    print("\n" + "=" * 60)
    print("4️⃣ ПРЕДЛАГАЕМОЕ РЕШЕНИЕ")
    print("=" * 60)
    
    if page.published and not template_found:
        print(f"Проблема: Шаблон '{page.template}.html' не существует")
        print(f"\nВарианты решения:")
        print(f"   A) Создать файл: templates/dynamic/{page.template}.html")
        print(f"   B) Изменить template в БД на существующий, например 'info_page'")
        
        fix = input("\nИсправить? (A/B/n): ")
        if fix.lower() == 'a':
            os.makedirs('templates/dynamic', exist_ok=True)
            with open(f'templates/dynamic/{page.template}.html', 'w', encoding='utf-8') as f:
                f.write(f"""{{% extends "base.html" %}}

    {{% block title %}}{{page.title}} - Красноярский ГАУ{{% endblock %}}

{{% block content %}}
<section class="page-header">
    <div class="container">
        <h1>{page.title}</h1>
    </div>
</section>

<section class="page-content">
    <div class="container">
        <div class="content-block">
            {{{{ page.content|safe }}}}
        </div>
    </div>
</section>
{{% endblock %}}""")
            print(f"✅ Шаблон создан: templates/dynamic/{page.template}.html")
            print("🔄 Перезапустите сервер и проверьте URL")
        elif fix.lower() == 'b':
            page.template = 'info_page'
            db.session.commit()
            print(f"✅ Template изменен на 'info_page'")
            print("🔄 Перезапустите сервер и проверьте URL")