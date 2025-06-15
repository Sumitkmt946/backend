from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# App Initialization
app = Flask(__name__)
CORS(app, origins=['http://localhost:4200'])  # Angular default

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy Instance
db = SQLAlchemy()
db.init_app(app)

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    entity_name = db.Column(db.String(255), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    contact_person = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='Open')
    phone_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'entityName': self.entity_name,
            'taskType': self.task_type,
            'time': self.time,
            'contactPerson': self.contact_person,
            'notes': self.notes,
            'status': self.status,
            'phoneNumber': self.phone_number,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

# Create DB & Add Sample Tasks
with app.app_context():
    db.create_all()
    if Task.query.count() == 0:
        sample_tasks = [
            Task(date='2025-06-14', entity_name='ABC Pvt Ltd', task_type='Call', time='10:00 AM',
                 contact_person='Ravi Kumar', notes='Follow-up call for demo', status='Open',
                 phone_number='+91-9876543210'),
            Task(date='2025-06-15', entity_name='XYZ Ltd', task_type='Meeting', time='02:00 PM',
                 contact_person='Suresh Sharma', notes='Client presentation', status='Closed')
        ]
        db.session.bulk_save_objects(sample_tasks)
        db.session.commit()
        print("✅ Sample data added!")

# Root Route
@app.route('/')
def root():
    return "Welcome to the Task Manager!"

# Base API Info
@app.route('/api', methods=['GET'])
def base_api():
    return jsonify({
        'message': 'Welcome to the Task Management API!',
        'endpoints': ['/api/health', '/api/tasks']
    })

# Health Check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Backend is running!', 'port': 5000})

# Get All Tasks (with optional search)
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        search = request.args.get('search', '')
        tasks_query = Task.query

        if search:
            tasks_query = tasks_query.filter(
                db.or_(
                    Task.entity_name.ilike(f'%{search}%'),
                    Task.contact_person.ilike(f'%{search}%')
                )
            )

        tasks = tasks_query.order_by(Task.created_at.desc()).all()
        return jsonify({'success': True, 'data': [task.to_dict() for task in tasks]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Create Task
@app.route('/api/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()
        required_fields = ['entityName', 'taskType', 'time', 'contactPerson', 'date', 'status']

        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

        new_task = Task(
            date=data['date'],
            entity_name=data['entityName'],
            task_type=data['taskType'],
            time=data['time'],
            contact_person=data['contactPerson'],
            notes=data.get('notes'),
            status=data['status'],
            phone_number=data.get('phoneNumber')
        )
        db.session.add(new_task)
        db.session.commit()

        return jsonify({'success': True, 'data': new_task.to_dict(), 'message': 'Task created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Get Single Task
@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        return jsonify(task.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update Task
@app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
def update_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()

        if 'status' in data:
            task.status = data['status']
        if 'entityName' in data:
            task.entity_name = data['entityName']
        if 'notes' in data:
            task.notes = data['notes']

        db.session.commit()
        return jsonify({'success': True, 'data': task.to_dict(), 'message': 'Task updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Delete Task
@app.route('/api/tasks/<int:task_id>', methods=['DELETE']) 
def delete_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Start Server
if __name__ == '__main__':
    if os.environ.get('VERCEL', None):
        app.run(debug=False)
    else:
        app.run(debug=True)
    print("🚀 Starting Flask Backend Server...")
    print("📍 Server URL: http://localhost:5000")
    print("🔗 API Base URL: http://localhost:5000/api")
    app.run(debug=True, host='0.0.0.0', port=5000)

