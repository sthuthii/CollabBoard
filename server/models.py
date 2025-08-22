from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    boards_owned = db.relationship('Board', backref='owner', lazy=True, foreign_keys='Board.owner_id')
    board_memberships = db.relationship('BoardMember', backref='user', lazy=True)
    assigned_tasks = db.relationship('Task', backref='assignee', lazy=True)
    messages = db.relationship('ChatMessage', backref='sender', lazy=True)
    def __repr__(self):
        return f'<User {self.username}>'

class Board(db.Model):
    __tablename__ = 'boards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('BoardMember', backref='board', lazy=True)
    tasks = db.relationship('Task', backref='board', lazy=True, cascade="all, delete-orphan")
    chat_messages = db.relationship('ChatMessage', backref='board', lazy=True, cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Board {self.name}>'

class BoardMember(db.Model):
    __tablename__ = 'board_members'
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='member')
    __table_args__ = (db.UniqueConstraint('board_id', 'user_id', name='_board_user_uc'),)
    def __repr__(self):
        return f'<BoardMember Board:{self.board_id} User:{self.user_id} Role:{self.role}>'

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='to_do')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def __repr__(self):
        return f'<Task {self.title} on Board {self.board_id}>'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return f'<ChatMessage User:{self.user_id} Board:{self.board_id} Time:{self.timestamp}>'