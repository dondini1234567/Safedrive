from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models.user import User
from app.models.file import File

@bp.route('/user', methods=['GET'])
@login_required
def get_user():
    """Get current user information"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'is_verified': current_user.is_verified,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None
    })

@bp.route('/user', methods=['PUT'])
@login_required
def update_user():
    """Update user information"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update user fields
    if 'first_name' in data:
        current_user.first_name = data['first_name']
    
    if 'last_name' in data:
        current_user.last_name = data['last_name']
    
    # Update password if provided
    if 'current_password' in data and 'new_password' in data:
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        current_user.set_password(data['new_password'])
    
    db.session.commit()
    
    return jsonify({'message': 'User updated successfully'})

@bp.route('/files/search', methods=['GET'])
@login_required
def search_files():
    """Search for files by name"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    files = File.query.filter(
        File.user_id == current_user.id,
        File.original_filename.ilike(f'%{query}%')
    ).all()
    
    return jsonify({
        'files': [file.to_dict() for file in files]
    })

@bp.route('/files/<int:file_id>/hint', methods=['PUT'])
@login_required
def update_file_hint(file_id):
    """Update the encryption hint for a file"""
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    data = request.get_json()
    
    if not data or 'hint' not in data:
        return jsonify({'error': 'No hint provided'}), 400
    
    file.encryption_hint = data['hint']
    db.session.commit()
    
    return jsonify({
        'message': 'File hint updated successfully',
        'file': file.to_dict()
    })

@bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get user statistics"""
    total_files = File.query.filter_by(user_id=current_user.id).count()
    
    # Get total size of all files
    total_size_query = db.session.query(db.func.sum(File.size)).filter(File.user_id == current_user.id)
    total_size = total_size_query.scalar() or 0
    
    # Get recent files
    recent_files = File.query.filter_by(user_id=current_user.id).order_by(File.created_at.desc()).limit(5).all()
    
    return jsonify({
        'total_files': total_files,
        'total_size': total_size,
        'recent_files': [file.to_dict() for file in recent_files]
    })
