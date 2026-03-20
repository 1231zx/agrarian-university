// Функции для админ панели

let currentTab = 'programs';

// Переключение вкладок
window.showTab = function(tabName) {
    console.log('Переключение на вкладку:', tabName);
    currentTab = tabName;
    
    // Скрыть все вкладки
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Убрать активность с кнопок
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Показать выбранную вкладку
    const tabElement = document.getElementById(`${tabName}-tab`);
    if (tabElement) {
        tabElement.classList.add('active');
    }
    
    // Найти и активировать правильную кнопку
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        const btnText = btn.textContent.toLowerCase();
        if ((tabName === 'programs' && btnText.includes('программы')) ||
            (tabName === 'news' && btnText.includes('новости')) ||
            (tabName === 'contacts' && btnText.includes('сообщения'))) {
            btn.classList.add('active');
        }
    });
    
    // Загрузить данные для выбранной вкладки
    if (tabName === 'programs') {
        loadPrograms();
    } else if (tabName === 'news') {
        loadNews();
    } else if (tabName === 'contacts') {
        loadContacts();
    }
};

// ===== ПРОГРАММЫ =====

function loadPrograms() {
    console.log('Загрузка программ...');
    const list = document.getElementById('programs-admin-list');
    if (!list) {
        console.error('Элемент programs-admin-list не найден');
        return;
    }
    
    list.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">Загрузка...</p>';
    
    fetch('/api/v1/programs')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Данные программ:', data);
            list.innerHTML = '';
            
            if (!data.programs || data.programs.length === 0) {
                list.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">Нет программ</p>';
                return;
            }
            
            data.programs.forEach(program => {
                const item = document.createElement('div');
                item.className = 'admin-item';
                item.innerHTML = `
                    <div class="admin-item-content">
                        <h3>${escapeHtml(program.name)}</h3>
                        <p><strong>Степень:</strong> ${escapeHtml(program.degree)}</p>
                        <p><strong>Длительность:</strong> ${escapeHtml(program.duration)}</p>
                        <p>${escapeHtml(program.description)}</p>
                    </div>
                    <div class="admin-item-actions">
                        <button class="btn-edit" onclick="editProgram(${program.id})">✏️ Редактировать</button>
                        <button class="btn-delete" onclick="deleteProgram(${program.id})">🗑️ Удалить</button>
                    </div>
                `;
                list.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Ошибка загрузки программ:', error);
            list.innerHTML = '<p style="text-align: center; color: #dc3545; padding: 2rem;">❌ Ошибка загрузки данных. Проверьте консоль.</p>';
            showNotification('Ошибка загрузки программ: ' + error.message, 'error');
        });
}

function saveProgram(e) {
    e.preventDefault();
    console.log('Сохранение программы...');
    
    const id = document.getElementById('program-id').value;
    const data = {
        name: document.getElementById('program-name').value,
        description: document.getElementById('program-description').value,
        duration: document.getElementById('program-duration').value,
        degree: document.getElementById('program-degree').value
    };
    
    // Валидация
    if (!data.name || !data.description || !data.duration || !data.degree) {
        showNotification('Заполните все поля!', 'error');
        return;
    }
    
    console.log('Данные для отправки:', data);
    
    const url = id ? `/api/v1/programs/${id}` : '/api/v1/programs';
    const method = id ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        console.log('Результат:', result);
        showNotification(result.message || 'Программа сохранена успешно!');
        resetProgramForm();
        loadPrograms();
    })
    .catch(error => {
        console.error('Ошибка при сохранении:', error);
        showNotification('Ошибка при сохранении: ' + error.message, 'error');
    });
}

function editProgram(id) {
    console.log('Редактирование программы:', id);
    
    fetch(`/api/v1/programs/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(program => {
            console.log('Программа для редактирования:', program);
            document.getElementById('program-id').value = program.id;
            document.getElementById('program-name').value = program.name;
            document.getElementById('program-description').value = program.description;
            document.getElementById('program-duration').value = program.duration;
            document.getElementById('program-degree').value = program.degree;
            
            const formTitle = document.querySelector('.admin-form h3');
            if (formTitle) {
                formTitle.textContent = 'Редактировать программу';
            }
            
            window.scrollTo({ top: 0, behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при загрузке программы', 'error');
        });
}

function deleteProgram(id) {
    if (!confirm('Вы уверены, что хотите удалить эту программу?')) return;
    
    console.log('Удаление программы:', id);
    
    fetch(`/api/v1/programs/${id}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        console.log('Результат удаления:', result);
        showNotification(result.message || 'Программа удалена');
        loadPrograms();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Ошибка при удалении: ' + error.message, 'error');
    });
}

window.resetProgramForm = function() {
    document.getElementById('program-form').reset();
    document.getElementById('program-id').value = '';
    const formTitle = document.querySelector('.admin-form h3');
    if (formTitle) {
        formTitle.textContent = 'Добавить новую программу';
    }
};

// ===== НОВОСТИ =====

function loadNews() {
    console.log('Загрузка новостей...');
    const list = document.getElementById('news-admin-list');
    if (!list) {
        console.error('Элемент news-admin-list не найден');
        return;
    }
    
    list.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">Загрузка...</p>';
    
    fetch('/api/v1/news')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Данные новостей:', data);
            list.innerHTML = '';
            
            if (!data.news || data.news.length === 0) {
                list.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">Нет новостей</p>';
                return;
            }
            
            data.news.forEach(newsItem => {
                const date = new Date(newsItem.published_at).toLocaleDateString('ru-RU');
                const item = document.createElement('div');
                item.className = 'admin-item';
                item.innerHTML = `
                    <div class="admin-item-content">
                        <h3>${escapeHtml(newsItem.title)}</h3>
                        <p><strong>Автор:</strong> ${escapeHtml(newsItem.author)} | <strong>Дата:</strong> ${date}</p>
                        <p>${escapeHtml(newsItem.content)}</p>
                    </div>
                    <div class="admin-item-actions">
                        <button class="btn-edit" onclick="editNews(${newsItem.id})">✏️ Редактировать</button>
                        <button class="btn-delete" onclick="deleteNews(${newsItem.id})">🗑️ Удалить</button>
                    </div>
                `;
                list.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Ошибка загрузки новостей:', error);
            list.innerHTML = '<p style="text-align: center; color: #dc3545; padding: 2rem;">❌ Ошибка загрузки данных. Проверьте консоль.</p>';
            showNotification('Ошибка загрузки новостей: ' + error.message, 'error');
        });
}

function saveNews(e) {
    e.preventDefault();
    console.log('Сохранение новости...');
    
    const id = document.getElementById('news-id').value;
    const data = {
        title: document.getElementById('news-title').value,
        content: document.getElementById('news-content').value,
        author: document.getElementById('news-author').value
    };
    
    // Валидация
    if (!data.title || !data.content || !data.author) {
        showNotification('Заполните все поля!', 'error');
        return;
    }
    
    console.log('Данные новости:', data);
    
    const url = id ? `/api/v1/news/${id}` : '/api/v1/news';
    const method = id ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        console.log('Результат:', result);
        showNotification(result.message || 'Новость сохранена успешно!');
        resetNewsForm();
        loadNews();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Ошибка при сохранении: ' + error.message, 'error');
    });
}

window.editNews = function(id) {
    console.log('Редактирование новости:', id);
    
    fetch(`/api/v1/news/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(newsItem => {
            console.log('Новость для редактирования:', newsItem);
            document.getElementById('news-id').value = newsItem.id;
            document.getElementById('news-title').value = newsItem.title;
            document.getElementById('news-content').value = newsItem.content;
            document.getElementById('news-author').value = newsItem.author;
            
            const formTitle = document.querySelector('.admin-form h3');
            if (formTitle) {
                formTitle.textContent = 'Редактировать новость';
            }
            
            // Переключиться на вкладку новостей
            window.showTab('news');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при загрузке новости', 'error');
        });
};

function deleteNews(id) {
    if (!confirm('Вы уверены, что хотите удалить эту новость?')) return;
    
    console.log('Удаление новости:', id);
    
    fetch(`/api/v1/news/${id}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        console.log('Результат удаления:', result);
        showNotification(result.message || 'Новость удалена');
        loadNews();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Ошибка при удалении: ' + error.message, 'error');
    });
}

window.resetNewsForm = function() {
    document.getElementById('news-form').reset();
    document.getElementById('news-id').value = '';
    const formTitle = document.querySelector('.admin-form h3');
    if (formTitle) {
        formTitle.textContent = 'Добавить новость';
    }
};

// ===== КОНТАКТЫ =====

function loadContacts() {
    console.log('Загрузка контактов...');
    const list = document.getElementById('contacts-admin-list');
    if (!list) {
        console.error('Элемент contacts-admin-list не найден');
        return;
    }
    
    list.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">Загрузка...</p>';
    
    fetch('/api/v1/contacts')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Данные контактов:', data);
            list.innerHTML = '';
            
            if (!data.contacts || data.contacts.length === 0) {
                list.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">Нет полученных сообщений</p>';
                return;
            }
            
            data.contacts.forEach(contact => {
                const date = new Date(contact.created_at).toLocaleDateString('ru-RU');
                const item = document.createElement('div');
                item.className = 'admin-item';
                item.innerHTML = `
                    <div class="admin-item-content">
                        <h3>${escapeHtml(contact.name)}</h3>
                        <p><strong>Email:</strong> ${escapeHtml(contact.email)} | <strong>Телефон:</strong> ${escapeHtml(contact.phone)}</p>
                        <p><strong>Дата:</strong> ${date}</p>
                        <p>${escapeHtml(contact.message)}</p>
                    </div>
                    <div class="admin-item-actions">
                        <button class="btn-delete" onclick="deleteContact(${contact.id})">🗑️ Удалить</button>
                    </div>
                `;
                list.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Ошибка загрузки контактов:', error);
            list.innerHTML = '<p style="text-align: center; color: #dc3545; padding: 2rem;">❌ Ошибка загрузки данных. Проверьте консоль.</p>';
            showNotification('Ошибка загрузки сообщений: ' + error.message, 'error');
        });
}

window.deleteContact = function(id) {
    if (!confirm('Вы уверены, что хотите удалить это сообщение?')) return;
    
    console.log('Удаление контакта:', id);
    
    fetch(`/api/v1/contacts/${id}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        console.log('Результат удаления:', result);
        showNotification(result.message || 'Сообщение удалено');
        loadContacts();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Ошибка при удалении: ' + error.message, 'error');
    });
};

// Вспомогательная функция для экранирования HTML
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Функция уведомлений
function showNotification(message, type = 'success') {
    // Удаляем предыдущее уведомление, если есть
    const oldNotification = document.querySelector('.notification');
    if (oldNotification) {
        oldNotification.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1.5rem 2.5rem;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        border-radius: 15px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        z-index: 10000;
        animation: slideInRight 0.4s ease-out;
        font-weight: 600;
        font-size: 1rem;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.4s ease-out';
        setTimeout(() => notification.remove(), 400);
    }, 3000);
}

// Добавляем стили для анимаций
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, инициализация админ панели...');
    
    // Привязка обработчиков форм
    const programForm = document.getElementById('program-form');
    if (programForm) {
        console.log('Форма программы найдена');
        programForm.addEventListener('submit', saveProgram);
    }
    
    const newsForm = document.getElementById('news-form');
    if (newsForm) {
        console.log('Форма новостей найдена');
        newsForm.addEventListener('submit', saveNews);
    }
    
    // По умолчанию показываем вкладку программ
    window.showTab('programs');
});