import os
import re

# Укажите путь к папке со старыми HTML файлами
SOURCE_FOLDER = 'old_pages'  # папка с 170+ файлами
OUTPUT_FILE = 'pages_data.py'

def extract_content_from_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлекаем заголовок из <title>
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1).replace(' - ООО Аграрный Университет', '').strip() if title_match else 'Без названия'
    
    # Извлекаем контент из {% block content %}
    block_match = re.search(r'{% block content %}(.*?){% endblock %}', content, re.DOTALL)
    body_content = block_match.group(1).strip() if block_match else content
    
    # Очищаем контент для сохранения в Python
    body_content = body_content.replace("'''", "\\'\\'\\'")
    
    return title, body_content

def detect_template(filename, content):
    if 'applicant' in filename.lower() or 'admission' in filename.lower() or 'поступающему' in content[:200]:
        return 'applicant_section'
    elif 'student' in filename.lower() or 'студенту' in content[:200]:
        return 'student_section'
    elif 'science' in filename.lower() or 'наука' in content[:200]:
        return 'science_section'
    elif 'institute' in filename.lower() or 'институт' in content[:200]:
        return 'institute'
    else:
        return 'info_page'

def detect_parent(filename, content):
    if 'university' in filename.lower() or 'университет' in content[:200]:
        return 'university_main'
    elif 'applicant' in filename.lower() or 'admission' in filename.lower():
        return 'applicant_main'
    elif 'student' in filename.lower():
        return 'student_main'
    elif 'science' in filename.lower():
        return 'science_main'
    else:
        return None

# Собираем все HTML файлы
html_files = []
for root, dirs, files in os.walk(SOURCE_FOLDER):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

print(f"📁 Найдено HTML файлов: {len(html_files)}")

# Генерируем словарь страниц
pages_dict = {}

for filepath in html_files:
    filename = os.path.basename(filepath)
    slug = filename.replace('.html', '')
    
    title, content = extract_content_from_html(filepath)
    template = detect_template(filename, content)
    parent = detect_parent(filename, content)
    
    pages_dict[slug] = {
        'title': title,
        'template': template,
        'parent': parent,
        'content': content
    }
    
    print(f"✅ {slug} -> {title[:40]}...")

# Сохраняем в Python файл
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("# Автоматически сгенерированный файл со всеми страницами\n")
    f.write("PAGES = {\n")
    
    for slug, data in pages_dict.items():
        f.write(f"    '{slug}': {{\n")
        f.write(f"        'title': '{data['title']}',\n")
        f.write(f"        'template': '{data['template']}',\n")
        f.write(f"        'parent': {repr(data['parent'])},\n")
        f.write(f"        'content': '''{data['content']}''',\n")
        f.write(f"    }},\n")
    
    f.write("}\n")

print(f"\n🎉 Готово! Создан файл {OUTPUT_FILE}")
print(f"📊 Всего страниц: {len(pages_dict)}")