import os
from flask import Flask, render_template, url_for, request, redirect, session
from abc import ABC, abstractmethod

# Интерфейс для пользователя
class IUser(ABC):
    @abstractmethod
    def get_role(self):
        pass

    @abstractmethod
    def get_events(self):
        pass

# Класс для пользователей
class User(IUser):
    def __init__(self, fio, login, password, **kwargs):
        self.fio = fio
        self.login = login
        self.password = password
        self.events = kwargs.get('events', [])

    def get_events(self):
        return self.events

# Класс организатора
class Organizer(User):
    def __init__(self, fio, login, password, company, **kwargs):
        super().__init__(fio, login, password, **kwargs)
        self.company = company

    def get_role(self):
        return 'Организатор'

# Класс участника
class Participant(User):
    def __init__(self, fio, login, password, workplace, **kwargs):
        super().__init__(fio, login, password, **kwargs)
        self.workplace = workplace

    def get_role(self):
        return 'Участник'

# Класс модератора
class Moderator(User):
    def __init__(self, fio, login, password, tools, **kwargs):
        super().__init__(fio, login, password, **kwargs)
        self.tools = tools

    def get_role(self):
        return 'Модератор'

# Интерфейс для аутентификации
class IAuthenticator(ABC):
    @abstractmethod
    def authenticate(self, login, password):
        pass

# Класс аутентификации
class Authenticator(IAuthenticator):
    def __init__(self, users):
        self.users = users

    def authenticate(self, login, password):
        user = next((u for u in self.users if u.login == login and u.password == password), None)
        return user

# Интерфейс для управления событиями
class IEventManager(ABC):
    @abstractmethod
    def get_events(self):
        pass

# Класс управления событиями
class EventManager(IEventManager):
    def __init__(self, events):
        self.events = events

    def get_events(self):
        return self.events

# Класс для событий
class Event:
    def __init__(self, event_id, name, description, date, time, organizer, participants, max_participants, event_type, duration, formats):
        self.id = event_id
        self.name = name
        self.description = description
        self.date = date
        self.time = time
        self.organizer = organizer
        self.participants = participants
        self.max_participants = max_participants
        self.type = event_type
        self.duration = duration
        self.formats = formats

# Класс для приложения
class App:
    def __init__(self, flask_app, authenticator, event_manager):
        self.app = flask_app
        self.authenticator = authenticator
        self.event_manager = event_manager
        self.users = [
            Organizer('Иван Иванов', 'organizer1', '12345', 'ООО Пример', events=['Python Conf 2024']),
            Participant('Анна Смирнова', 'participant1', '54321', 'Техникум Пример', events=['Python Conf 2024']),
            Moderator('Олег Петров', 'moderator1', 'pass123', ['Управление чатом', 'Мониторинг сессии']),
        ]
        self.configure_routes()

    def configure_routes(self):
        @self.app.route('/')
        def index():
            user = session.get('user')
            return render_template('index.html', user=user)

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                login = request.form['login']
                password = request.form['password']

                user = self.authenticator.authenticate(login, password)
                if user:
                    session['user'] = session['user'] = {
                        'role': user.get_role(),
                        'fio': user.fio,
                        'login': user.login,
                        'password': user.password,
                        'events': user.events,
                        # Добавьте дополнительные данные в зависимости от роли
                        'company': getattr(user, 'company', None),
                        'workplace': getattr(user, 'workplace', None),
                        'tools': getattr(user, 'tools', None),
                    }
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error='Неверный логин или пароль')

            return render_template('login.html')

        @self.app.route('/logout')
        def logout():
            session.pop('user', None)
            return redirect(url_for('index'))

        @self.app.route('/profile')
        def profile():
            user = session.get('user')
            if not user:
                return redirect(url_for('login'))

            # Проверяем роль пользователя, для создания правильного экземпляра
            if user.get('role') == 'Организатор':
                user = Organizer(**user)
            elif user.get('role') == 'Участник':
                user = Participant(**user)
            elif user.get('role') == 'Модератор':
                user = Moderator(**user)

            return render_template('profile.html', user=user)

        @self.app.route('/events')
        def events():
            user = session.get('user')
            return render_template('event_details.html', events=self.event_manager.get_events(), user=user)

        @self.app.route('/users')
        def users_list():
            user = session.get('user')
            organizers = [user for user in self.users if user.get_role() == 'Организатор']
            participants = [user for user in self.users if user.get_role() == 'Участник']
            moderators = [user for user in self.users if user.get_role() == 'Модератор']
            return render_template('users.html', organizers=organizers, participants=participants,
                                   moderators=moderators, user=user)

        @self.app.route('/events/<int:event_id>')
        def event_details(event_id):
            user = session.get('user')
            event = next((e for e in self.event_manager.get_events() if e.id == event_id), None)
            return render_template('events.html', event=event, user=user)


if __name__ == '__main__':
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    # Инстанцируем менеджеры с правильными списками пользователей и событий
    authenticator = Authenticator([
        Organizer('Иван Иванов', 'organizer1', '12345', 'ООО Пример', events=['Python Conf 2024']),
        Participant('Анна Смирнова', 'participant1', '54321', 'Техникум Пример', events=['Python Conf 2024']),
        Moderator('Олег Петров', 'moderator1', 'pass123', ['Управление чатом', 'Мониторинг сессии']),
    ])
    event_manager = EventManager([
        Event(1, 'Конференция по Python', 'Обсуждение новых возможностей Python 3.12 и лучших практик.', '2024-12-20', '10:00', 'Иван Иванов', ['Анна Смирнова', 'Олег Петров'], 100, 'Открытое', '3 часа', ['Презентации', 'Видео']),
        Event(2, 'Вебинар по Flask', 'Разработка веб-приложений с использованием Flask.', '2024-12-25', '15:00', 'Анна Смирнова', ['Иван Иванов'], 50, 'Закрытое', '2 часа', ['Презентации']),
    ])

    # Создаем экземпляр приложения
    app_instance = App(app, authenticator, event_manager)
    app.run(debug=True)
