import psycopg2
import os

# Строка подключения к БД на Render
DATABASE_URL = "postgresql://argagka_user:ti0ahEFqMthvNjh9QZSkNcvyCRDgPJAa@dpg-d6uqtukr85hc738vfds0-a/argagka"

def add_pages():
    try:
        # Подключаемся к БД
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Сначала проверим, есть ли родительские страницы
        cur.execute("SELECT id, slug FROM pages WHERE slug IN ('university_main', 'applicant_main', 'student_main')")
        parents = cur.fetchall()
        
        parent_ids = {}
        for pid, pslug in parents:
            parent_ids[pslug] = pid
        
        if not parent_ids:
            print("❌ Родительские страницы не найдены! Сначала создайте их через админ-панель.")
            print("   Нужно создать: university_main, applicant_main, student_main")
            return
        
        print(f"✅ Найдены родители: {parent_ids}")
        
        # Данные для добавления страниц
        pages_to_add = [
            ('admission_regulations', 'Нормативные документы', 
             '<h2>Основные документы приема 2026 года</h2><ul><li>Правила приема в Красноярский ГАУ на 2026 год</li><li>Перечень вступительных испытаний</li><li>Порядок учета индивидуальных достижений</li></ul>', 
             'applicant_section', parent_ids.get('applicant_main')),
            
            ('exam_schedule', 'Расписание экзаменов', 
             '<p>Расписание вступительных испытаний будет опубликовано после завершения приема документов.</p><p>Телефон: +7 (391) 222-07-68</p>', 
             'applicant_section', parent_ids.get('applicant_main')),
            
            ('enrollment_info', 'Сведения о зачислении', 
             '<h2>Сведения о зачислении 2026</h2><p>Даты публикации: 5 и 10 августа</p>', 
             'applicant_section', parent_ids.get('applicant_main')),
            
            ('university_popechitelskiy', 'Попечительский совет', 
             '<h2>Попечительский совет</h2><p>Создан для содействия развитию университета</p>', 
             'info_page', parent_ids.get('university_main')),
            
            ('university_anticorruption', 'Противодействие коррупции', 
             '<h2>Противодействие коррупции</h2><p>Телефон доверия: +7 (391) 227-09-81</p>', 
             'info_page', parent_ids.get('university_main')),
            
            ('university_parent_council', 'Совет родителей', 
             '<h2>Совет родителей</h2><p>Email: parents@kgau.ru</p>', 
             'info_page', parent_ids.get('university_main')),
            
            ('university_vesti_archive', 'Архив журнала «Вести Красноярского ГАУ»', 
             '<h2>Архив журнала</h2><p><a href="https://www.kgau.ru/university/nasha-pressa/archive/" target="_blank">Перейти к архиву →</a></p>', 
             'info_page', parent_ids.get('university_main')),
        ]
        
        # Добавляем страницы
        added = 0
        skipped = 0
        
        for slug, title, content, template, parent_id in pages_to_add:
            if parent_id is None:
                print(f"⚠️ Пропущено {slug}: родитель не найден")
                skipped += 1
                continue
            
            # Проверяем, существует ли уже страница
            cur.execute("SELECT id FROM pages WHERE slug = %s", (slug,))
            if cur.fetchone():
                print(f"⚠️ Пропущено {slug}: уже существует")
                skipped += 1
                continue
            
            # Вставляем
            cur.execute("""
                INSERT INTO pages (slug, title, content, template, parent_id, published, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, true, NOW(), NOW())
            """, (slug, title, content, template, parent_id))
            print(f"✅ Добавлено: {slug} - {title}")
            added += 1
        
        conn.commit()
        print(f"\n🎉 Готово! Добавлено: {added}, Пропущено: {skipped}")
        
        # Показываем все страницы
        cur.execute("SELECT slug, title, template FROM pages ORDER BY template, title")
        all_pages = cur.fetchall()
        print("\n📋 Все страницы в БД:")
        for slug, title, template in all_pages:
            print(f"   {slug} ({template}) - {title}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    add_pages()