from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask import Blueprint
from flask_debugtoolbar import DebugToolbarExtension
from datetime import datetime
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.secret_key = '12345678'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anime_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = 'simple'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
cache = Cache(app)
anime_bp = Blueprint('anime', __name__)
app.debug = True
toolbar = DebugToolbarExtension(app)

# В командной строке:
# flask db init
# flask db migrate -m "Initial migration."
# flask db upgrade


# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), default='default_avatar.png')
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)

    # Связи
    reviews = relationship('Review', back_populates='user')
    forum_posts = relationship('ForumPost', back_populates='author')
    favorites = relationship('Favorite', back_populates='user')

class Anime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    title_original = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200))
    trailer_url = db.Column(db.String(200))
    release_date = db.Column(db.Date)
    total_episodes = db.Column(db.Integer)
    status = db.Column(db.String(20))  # Онгоинг, Завершен и т.д.

    # Связи
    reviews = relationship('Review', back_populates='anime')
    characters = relationship('Character', back_populates='anime')


class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_original = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    anime_id = db.Column(db.Integer, db.ForeignKey('anime.id'))

    anime = relationship('Anime', back_populates='characters')


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    anime_id = db.Column(db.Integer, db.ForeignKey('anime.id'), nullable=False)

    user = relationship('User', back_populates='reviews')
    anime = relationship('Anime', back_populates='reviews')


class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    author = relationship('User', back_populates='forum_posts')
    comments = relationship('ForumComment', back_populates='post')


class ForumComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)

    user = relationship('User')
    post = relationship('ForumPost', back_populates='comments')


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    anime_id = db.Column(db.Integer, db.ForeignKey('anime.id'), nullable=False)

    user = relationship('User', back_populates='favorites')
    anime = relationship('Anime')


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50))  # Аниме, Манга, Фильм и т.д.


# Создание базы данных и таблиц
with app.app_context():
    db.create_all()
    print('База данных и таблицы созданы!')

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/anime/add', methods=['GET', 'POST'])
def add_anime():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        genre = request.form['genre']
        image_url = request.form['image_url']

        new_anime = Anime(title=title, description=description, genre=genre, image_url=image_url)
        db.session.add(new_anime)
        db.session.commit()
        flash('Аниме добавлено успешно!')
        return redirect(url_for('anime_list'))

    return render_template('anime/add.html')

@anime_bp.route('/anime')
@app.route('/anime')
def anime_list():
    animes = Anime.query.with_entities(Anime.title, Anime.image_url).all()
    return render_template('anime.html', animes=animes)

app.register_blueprint(anime_bp)

# Редактирование аниме
@app.route('/anime/edit/<int:anime_id>', methods=['GET', 'POST'])
def edit_anime(anime_id):
    anime = Anime.query.get_or_404(anime_id)

    if request.method == 'POST':
        anime.title = request.form['title']
        anime.description = request.form['description']
        anime.genre = request.form['genre']
        anime.image_url = request.form['image_url']

        db.session.commit()
        flash('Аниме обновлено успешно!')
        return redirect(url_for('anime_list'))

    return render_template('anime/edit.html', anime=anime)

# Удаление аниме
@app.route('/anime/delete/<int:anime_id>', methods=['POST'])
def delete_anime(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    db.session.delete(anime)
    db.session.commit()
    flash('Аниме удалено успешно!')
    return redirect(url_for('anime_list'))

@app.route('/manga')
def manga():
    return render_template("manga.html")

@app.route('/news')
def news():
    return render_template("news.html")

@app.route('/ratings')
def ratings():
    return render_template("ratings.html")

@app.route('/forum')
def forum():
    return render_template("forum.html")

@app.route('/profile')
def profile():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        return render_template("profile.html", username=user.username, user=user)
    else:
        flash('Пожалуйста, войдите в систему, чтобы просмотреть свой профиль.')
        return redirect(url_for('login'))

@app.route('/characters')
def characters():
    return render_template("characters.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Пользователь с таким именем уже существует.')
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['username'] = username
            flash('Вы успешно вошли в систему!')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из системы.')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def exception_handler(error):
    db.session.rollback()
    return render_template('500.html'), 500

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200


@app.route('/anime/<int:anime_id>')
def anime_detail(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    reviews = Review.query.filter_by(anime_id=anime_id).all()
    characters = Character.query.filter_by(anime_id=anime_id).all()
    return render_template('anime/detail.html', anime=anime, reviews=reviews, characters=characters)


@app.route('/character/<int:character_id>')
def character_detail(character_id):
    character = Character.query.get_or_404(character_id)
    return render_template('characters/detail.html', character=character)


@app.route('/add_review/<int:anime_id>', methods=['POST'])
def add_review(anime_id):
    if 'username' not in session:
        flash('Пожалуйста, войдите в систему, чтобы оставить отзыв.')
        return redirect(url_for('login'))

    rating = request.form['rating']
    comment = request.form['comment']
    user = User.query.filter_by(username=session['username']).first()

    new_review = Review(
        user_id=user.id,
        anime_id=anime_id,
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()

    flash('Отзыв успешно добавлен!')
    return redirect(url_for('anime_ detail', anime_id=anime_id))


@app.route('/favorite/<int:anime_id>', methods=['POST'])
def add_favorite(anime_id):
    if 'username' not in session:
        flash('Пожалуйста, войдите в систему, чтобы добавить в избранное.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    favorite = Favorite.query.filter_by(user_id=user.id, anime_id=anime_id).first()

    if favorite:
        flash('Это аниме уже в вашем избранном.')
    else:
        new_favorite = Favorite(user_id=user.id, anime_id=anime_id)
        db.session.add(new_favorite)
        db.session.commit()
        flash('Аниме добавлено в избранное!')

    return redirect(url_for('anime_detail', anime_id=anime_id))


@app.route('/forum/<int:post_id>')
def forum_post_detail(post_id):
    post = ForumPost.query.get_or_404(post_id)
    comments = ForumComment.query.filter_by(post_id=post_id).all()
    return render_template('forum/detail.html', post=post, comments=comments)


@app.route('/add_forum_post', methods=['GET', 'POST'])
def add_forum_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user = User.query.filter_by(username=session['username']).first()

        new_post = ForumPost(title=title, content=content, user_id=user.id)
        db.session.add(new_post)
        db.session.commit()
        flash('Пост успешно добавлен!')
        return redirect(url_for('forum'))

    return render_template('forum/add_post.html')


@app.route('/add_forum_comment/<int:post_id>', methods=['POST'])
def add_forum_comment(post_id):
    if 'username' not in session:
        flash('Пожалуйста, войдите в систему, чтобы оставить комментарий.')
        return redirect(url_for('login'))

    content = request.form['content']
    user = User.query.filter_by(username=session['username']).first()

    new_comment = ForumComment(content=content, user_id=user.id, post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()

    flash('Комментарий успешно добавлен!')
    return redirect(url_for('forum_post_detail', post_id=post_id))


if __name__ == '__main__':
    app.run(debug=True)