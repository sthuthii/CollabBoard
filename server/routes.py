from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import db, User, Board, BoardMember, Task, ChatMessage # Import models
from . import bcrypt # Import bcrypt from the main app factory

# Create a Blueprint for our API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Utility Functions
def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed_password, password):
    return bcrypt.check_password_hash(hashed_password, password)

# User Authentication Routes
@api_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not all([username, email, password]):
        return jsonify({"msg": "Missing username, email, or password"}), 400
    user_exists = User.query.filter_by(username=username).first() is not None
    email_exists = User.query.filter_by(email=email).first() is not None
    if user_exists or email_exists:
        return jsonify({"msg": "Username or email already exists"}), 409
    hashed_password = hash_password(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "User created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred", "error": str(e)}), 500

@api_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username_or_email = data.get('username_or_email')
    password = data.get('password')
    if not username_or_email or not password:
        return jsonify({"msg": "Missing username/email or password"}), 400
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
    # ... inside the login_user function
    if user and check_password(user.password_hash, password):
    # Pass the user's ID as the identity
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token, username=user.username), 200
    else:
        return jsonify({"msg": "Bad username/email or password"}), 401

@api_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    print("Received headers:", request.headers)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at
    }), 200

# Board Management Routes
@api_bp.route('/boards', methods=['POST'])
@jwt_required()
def create_board():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    board_name = data.get('name')
    if not board_name:
        return jsonify({"msg": "Board name is required"}), 400
    try:
        new_board = Board(name=board_name, owner_id=current_user_id)
        db.session.add(new_board)
        db.session.commit()
        owner_membership = BoardMember(board_id=new_board.id, user_id=current_user_id, role='owner')
        db.session.add(owner_membership)
        db.session.commit()
        return jsonify({"msg": "Board created successfully", "board_id": new_board.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred", "error": str(e)}), 500

@api_bp.route('/boards', methods=['GET'])
@jwt_required()
def get_user_boards():
    current_user_id = get_jwt_identity()
    user_memberships = BoardMember.query.filter_by(user_id=current_user_id).all()
    boards = []
    for membership in user_memberships:
        board = Board.query.get(membership.board_id)
        if board:
            boards.append({
                "id": board.id,
                "name": board.name,
                "owner_id": board.owner_id
            })
    return jsonify(boards), 200

@api_bp.route('/boards/<int:board_id>', methods=['GET'])
@jwt_required()
def get_board_details(board_id):
    current_user_id = get_jwt_identity()
    board = Board.query.get(board_id)
    if not board:
        return jsonify({"msg": "Board not found"}), 404
    is_member = BoardMember.query.filter_by(board_id=board_id, user_id=current_user_id).first()
    if not is_member:
        return jsonify({"msg": "Unauthorized to view this board"}), 403
    board_members = BoardMember.query.filter_by(board_id=board_id).all()
    members_list = []
    for member in board_members:
        user = User.query.get(member.user_id)
        if user:
            members_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": member.role
            })
    tasks = Task.query.filter_by(board_id=board_id).order_by(Task.status).all()
    tasks_list = []
    for task in tasks:
        tasks_list.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "assignee_id": task.assignee_id,
            "status": task.status,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        })
    return jsonify({
        "id": board.id,
        "name": board.name,
        "owner_id": board.owner_id,
        "members": members_list,
        "tasks": tasks_list
    }), 200

#---------------Task management routes------------------
# --- Task Management Routes ---
@api_bp.route('/boards/<int:board_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(board_id):
    """Create a new task on a specific board."""
    current_user_id = get_jwt_identity()
    board = Board.query.get(board_id)

    if not board:
        return jsonify({"msg": "Board not found"}), 404

    # Check if user is a member of the board
    is_member = BoardMember.query.filter_by(board_id=board_id, user_id=current_user_id).first()
    if not is_member:
        return jsonify({"msg": "Unauthorized to create a task on this board"}), 403

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    assignee_id = data.get('assignee_id')

    if not title:
        return jsonify({"msg": "Task title is required"}), 400

    # Optional: Validate assignee_id if provided
    if assignee_id:
        assignee = User.query.get(assignee_id)
        if not assignee:
            return jsonify({"msg": "Assignee not found"}), 404
        # Optional: Check if assignee is also a member of the board
        is_assignee_member = BoardMember.query.filter_by(board_id=board_id, user_id=assignee_id).first()
        if not is_assignee_member:
            return jsonify({"msg": "Assignee is not a member of this board"}), 400

    try:
        new_task = Task(
            board_id=board_id,
            title=title,
            description=description,
            assignee_id=assignee_id,
            status='to_do' # Default status
        )
        db.session.add(new_task)
        db.session.commit()
        return jsonify({
            "msg": "Task created successfully",
            "task_id": new_task.id,
            "title": new_task.title
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred", "error": str(e)}), 500


@api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update a specific task (e.g., move to another column)."""
    current_user_id = get_jwt_identity()
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404

    # Check if user is a member of the board this task belongs to
    is_member = BoardMember.query.filter_by(board_id=task.board_id, user_id=current_user_id).first()
    if not is_member:
        return jsonify({"msg": "Unauthorized to update this task"}), 403

    data = request.get_json()
    
    # Update fields only if they exist in the request body
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']
    if 'assignee_id' in data:
        task.assignee_id = data['assignee_id']

    try:
        db.session.commit()
        return jsonify({"msg": "Task updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred", "error": str(e)}), 500

# --- User/Member Management Routes ---
@api_bp.route('/users/search', methods=['GET'])
@jwt_required()
def search_users():
    """Search for users by username or email."""
    query = request.args.get('q')
    if not query:
        return jsonify([]), 200 # Return empty list if no query
    
    users = User.query.filter(
        (User.username.ilike(f'%{query}%')) | 
        (User.email.ilike(f'%{query}%'))
    ).all()

    users_list = [{
        "id": user.id,
        "username": user.username,
        "email": user.email
    } for user in users]

    return jsonify(users_list), 200

@api_bp.route('/boards/<int:board_id>/members', methods=['POST'])
@jwt_required()
def add_board_member(board_id):
    """Add a new member to a board."""
    current_user_id = get_jwt_identity()
    board = Board.query.get(board_id)
    if not board:
        return jsonify({"msg": "Board not found"}), 404

    # Check if the current user is the owner of the board
    if board.owner_id != current_user_id:
        return jsonify({"msg": "Only the board owner can add new members"}), 403

    data = request.get_json()
    new_member_id = data.get('user_id')
    if not new_member_id:
        return jsonify({"msg": "User ID is required"}), 400

    # Ensure the user exists
    new_user = User.query.get(new_member_id)
    if not new_user:
        return jsonify({"msg": "User not found"}), 404

    # Check if the user is already a member
    is_already_member = BoardMember.query.filter_by(board_id=board_id, user_id=new_member_id).first()
    if is_already_member:
        return jsonify({"msg": "User is already a member of this board"}), 409

    try:
        new_membership = BoardMember(board_id=board_id, user_id=new_member_id, role='member')
        db.session.add(new_membership)
        db.session.commit()
        return jsonify({
            "msg": "Member added successfully", 
            "username": new_user.username
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred", "error": str(e)}), 500