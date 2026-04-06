import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Page

app = create_app()

def clean_content(html_content, page_title):
    """Удаляет дублирующиеся заголовки из контента"""
    
    # Удаляем <section class="page-header">...</section>
    pattern1 = r'<section class="page-header">.*?</section>'
    html_content = re.sub(pattern1, '', html_content, flags=re.DOTALL)
    
    # Удаляем заголовок h1 в начале, если он совпадает с названием страницы
    pattern2 = rf'<h1>{re.escape(page_title)}</h1>'
    html_content = re.sub(pattern2, '', html_content)
    
    # Удаляем пустые строки в начале
    html_content = html_content.strip()
    
    # Если после очистки ничего не осталось, возвращаем заглушку
    if not html_content:
        html_content = f'<h2>О кафедре</h2><p>Информация в разработке.</p>'
    
    return html_content

def fix_all_pages():
    with app.app_context():
        # Получаем все страницы типа department и institute
        pages = Page.query.filter(Page.template.in_(['department', 'institute'])).all()
        
        updated = 0
        for page in pages:
            original_content = page.content
            
            cleaned = clean_content(original_content, page.title)
            
            if cleaned != original_content:
                page.content = cleaned
                db.session.commit()
                updated += 1
                print(f'✅ Очищен дубль: {page.title}')
        
        print(f'\n🎉 Очищено страниц: {updated}')

if __name__ == '__main__':
    fix_all_pages()