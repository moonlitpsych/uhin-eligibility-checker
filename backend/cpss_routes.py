"""
CPSS Dashboard API Routes
Handles pod management, participant tracking, sessions, and billing
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
import sqlite3
from backend.cpss_database import CPSSDashboardDB
from backend.auth import jwt_required, role_required

# Create Blueprint
cpss_api = Blueprint('cpss_api', __name__)

# Initialize database
cpss_db = CPSSDashboardDB()

# ============= POD MANAGEMENT =============

@cpss_api.route('/api/cpss/pods', methods=['GET'])
@jwt_required
def get_user_pods():
    """Get all pods managed by the current CPSS user"""
    cpss_user_id = request.current_user.get('user_id')

    conn = sqlite3.connect(cpss_db.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.*, COUNT(pp.id) as participant_count
        FROM cm_pods p
        LEFT JOIN pod_participants pp ON p.id = pp.pod_id AND pp.status = 'active'
        WHERE p.cpss_user_id = ? AND p.status = 'active'
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''', (cpss_user_id,))

    pods = []
    for row in cursor.fetchall():
        pods.append({
            'id': row[0],
            'name': row[1],
            'participant_count': row[-1],
            'max_participants': row[7],
            'start_date': row[4],
            'status': row[6]
        })

    conn.close()
    return jsonify({'pods': pods})

@cpss_api.route('/api/cpss/pods', methods=['POST'])
@jwt_required
def create_pod():
    """Create a new CM pod"""
    data = request.json
    cpss_user_id = request.current_user.get('user_id')

    try:
        pod_id = cpss_db.create_pod(
            cpss_user_id=cpss_user_id,
            pod_name=data.get('pod_name'),
            start_date=data.get('start_date'),
            max_participants=data.get('max_participants', 8)
        )

        return jsonify({
            'success': True,
            'pod_id': pod_id,
            'message': 'Pod created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@cpss_api.route('/api/cpss/pods/<int:pod_id>/participants', methods=['GET'])
@jwt_required
def get_pod_participants(pod_id):
    """Get all participants in a specific pod"""
    try:
        participants = cpss_db.get_pod_participants(pod_id)

        # Enhance with progress data
        for participant in participants:
            progress = cpss_db.get_participant_progress(participant['id'])
            participant['attendance_rate'] = progress.get('attendance_rate', 0)
            participant['last_test_date'] = progress.get('last_test_date')
            participant['progress_phase'] = progress.get('progress_phase')

        return jsonify({'participants': participants})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@cpss_api.route('/api/cpss/pods/<int:pod_id>/add-participant', methods=['POST'])
@jwt_required
def add_participant(pod_id):
    """Add a participant to a pod"""
    data = request.json
    enrollment_id = data.get('enrollment_id')

    if not enrollment_id:
        return jsonify({'error': 'Enrollment ID required'}), 400

    try:
        participant_id = cpss_db.add_participant_to_pod(pod_id, enrollment_id)
        return jsonify({
            'success': True,
            'participant_id': participant_id,
            'message': 'Participant added to pod'
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============= PARTICIPANT TRACKING =============

@cpss_api.route('/api/cpss/participants/<int:participant_id>/progress', methods=['GET'])
@jwt_required
def get_participant_progress(participant_id):
    """Get comprehensive progress data for a participant"""
    try:
        progress = cpss_db.get_participant_progress(participant_id)
        return jsonify(progress)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@cpss_api.route('/api/cpss/participants/<int:participant_id>/update-phase', methods=['POST'])
@jwt_required
def update_participant_phase(participant_id):
    """Update participant's progress phase"""
    data = request.json
    new_phase = data.get('phase')

    if new_phase not in ['phase_1', 'phase_2', 'phase_3', 'graduated']:
        return jsonify({'error': 'Invalid phase'}), 400

    # Update phase in database
    conn = sqlite3.connect(cpss_db.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE pod_participants
        SET progress_phase = ?
        WHERE id = ?
    ''', (new_phase, participant_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'new_phase': new_phase})

# ============= SESSION MANAGEMENT =============

@cpss_api.route('/api/cpss/sessions/schedule', methods=['POST'])
@jwt_required
def schedule_session():
    """Schedule a group session"""
    data = request.json

    try:
        session_id, session_uuid = cpss_db.schedule_group_session(
            pod_id=data.get('pod_id'),
            scheduled_time=datetime.fromisoformat(data.get('scheduled_time')),
            session_type=data.get('session_type'),
            billing_code=data.get('billing_code')
        )

        return jsonify({
            'success': True,
            'session_id': session_id,
            'session_uuid': session_uuid,
            'message': 'Session scheduled successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@cpss_api.route('/api/cpss/sessions/<int:session_id>/start', methods=['POST'])
@jwt_required
def start_session(session_id):
    """Start a scheduled session and generate video room"""
    # In production, integrate with video service (Twilio, Agora, etc.)
    video_room_id = f"room_{session_id}_{datetime.now().timestamp()}"

    conn = sqlite3.connect(cpss_db.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE group_sessions
        SET actual_start_time = ?,
            video_room_id = ?,
            status = 'in_progress'
        WHERE id = ?
    ''', (datetime.now(), video_room_id, session_id))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'video_room_id': video_room_id,
        'video_url': f"/video/join/{video_room_id}"  # Placeholder URL
    })

@cpss_api.route('/api/cpss/sessions/<int:session_id>/attendance', methods=['POST'])
@jwt_required
def mark_attendance(session_id):
    """Mark attendance for session participants"""
    data = request.json
    attendance_records = data.get('attendance', [])

    conn = sqlite3.connect(cpss_db.db_path)
    cursor = conn.cursor()

    for record in attendance_records:
        cursor.execute('''
            INSERT INTO session_attendance (
                session_id, participant_id, attendance_status,
                join_time, leave_time, duration_minutes,
                video_enabled, audio_enabled, participation_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            record.get('participant_id'),
            record.get('status'),
            record.get('join_time'),
            record.get('leave_time'),
            record.get('duration_minutes'),
            record.get('video_enabled', False),
            record.get('audio_enabled', False),
            record.get('participation_score')
        ))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'records_saved': len(attendance_records)})

# ============= DRUG TESTING =============

@cpss_api.route('/api/cpss/drug-tests', methods=['POST'])
@jwt_required
def record_drug_test():
    """Record a drug test observation"""
    data = request.json
    cpss_user_id = request.current_user.get('user_id')

    test_data = {
        'participant_id': data.get('participant_id'),
        'session_id': data.get('session_id'),
        'test_date': datetime.now(),
        'test_type': data.get('test_type', 'saliva'),
        'observed_by': cpss_user_id,
        'observation_method': data.get('observation_method', 'video'),
        'substances_tested': data.get('substances_tested', ['methamphetamine', 'cocaine']),
        'results': data.get('results'),
        'photo_url': data.get('photo_url'),
        'video_url': data.get('video_url'),
        'notes': data.get('notes')
    }

    try:
        test_id = cpss_db.record_drug_test(
            data.get('participant_id'),
            test_data
        )

        return jsonify({
            'success': True,
            'test_id': test_id,
            'message': 'Drug test recorded successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@cpss_api.route('/api/cpss/participants/<int:participant_id>/drug-tests', methods=['GET'])
@jwt_required
def get_participant_drug_tests(participant_id):
    """Get drug test history for a participant"""
    conn = sqlite3.connect(cpss_db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM drug_tests
        WHERE participant_id = ?
        ORDER BY test_date DESC
        LIMIT 20
    ''', (participant_id,))

    tests = []
    for row in cursor.fetchall():
        test = dict(row)
        test['substances_tested'] = json.loads(test['substances_tested'])
        test['results'] = json.loads(test['results'])
        tests.append(test)

    conn.close()
    return jsonify({'drug_tests': tests})

# ============= BEHAVIORAL ASSESSMENTS =============

@cpss_api.route('/api/cpss/assessments', methods=['POST'])
@jwt_required
def save_assessment():
    """Save a behavioral assessment"""
    data = request.json
    cpss_user_id = request.current_user.get('user_id')

    assessment_data = {
        'assessment_type': data.get('assessment_type'),
        'assessment_date': datetime.now(),
        'responses': data.get('responses'),
        'total_score': data.get('total_score'),
        'risk_level': data.get('risk_level'),
        'administered_by': cpss_user_id,
        'notes': data.get('notes')
    }

    try:
        assessment_id = cpss_db.save_assessment(
            data.get('participant_id'),
            assessment_data
        )

        return jsonify({
            'success': True,
            'assessment_id': assessment_id,
            'message': 'Assessment saved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@cpss_api.route('/api/cpss/assessments/templates/<assessment_type>', methods=['GET'])
@jwt_required
def get_assessment_template(assessment_type):
    """Get assessment template/questions"""
    templates = {
        'PHQ-9': {
            'title': 'Patient Health Questionnaire-9',
            'questions': [
                'Little interest or pleasure in doing things',
                'Feeling down, depressed, or hopeless',
                'Trouble falling or staying asleep, or sleeping too much',
                'Feeling tired or having little energy',
                'Poor appetite or overeating',
                'Feeling bad about yourself',
                'Trouble concentrating on things',
                'Moving or speaking slowly or being fidgety/restless',
                'Thoughts of self-harm'
            ],
            'scoring': 'Never (0), Several days (1), More than half the days (2), Nearly every day (3)'
        },
        'GAD-7': {
            'title': 'Generalized Anxiety Disorder-7',
            'questions': [
                'Feeling nervous, anxious, or on edge',
                'Not being able to stop or control worrying',
                'Worrying too much about different things',
                'Trouble relaxing',
                'Being so restless that it\'s hard to sit still',
                'Becoming easily annoyed or irritable',
                'Feeling afraid as if something awful might happen'
            ],
            'scoring': 'Not at all (0), Several days (1), More than half the days (2), Nearly every day (3)'
        }
    }

    template = templates.get(assessment_type)
    if not template:
        return jsonify({'error': 'Assessment type not found'}), 404

    return jsonify(template)

# ============= BILLING =============

@cpss_api.route('/api/cpss/billing/create', methods=['POST'])
@jwt_required
def create_billing_record():
    """Create a billing record for services"""
    data = request.json
    cpss_user_id = request.current_user.get('user_id')

    billing_data = {
        'participant_id': data.get('participant_id'),
        'session_id': data.get('session_id'),
        'service_date': data.get('service_date', datetime.now().date()),
        'cpt_code': data.get('cpt_code'),
        'units': data.get('units', 1),
        'duration_minutes': data.get('duration_minutes'),
        'provider_id': cpss_user_id,
        'documentation': data.get('documentation')
    }

    try:
        billing_id = cpss_db.create_billing_record(billing_data)

        return jsonify({
            'success': True,
            'billing_id': billing_id,
            'message': 'Billing record created'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@cpss_api.route('/api/cpss/billing/summary', methods=['GET'])
@jwt_required
def get_billing_summary():
    """Get billing summary for date range"""
    cpss_user_id = request.current_user.get('user_id')

    start_date = request.args.get('start_date',
                                  (datetime.now() - timedelta(days=30)).date())
    end_date = request.args.get('end_date', datetime.now().date())

    try:
        summary = cpss_db.get_billing_summary(cpss_user_id, start_date, end_date)

        # Calculate totals
        total_services = sum(s['service_count'] for s in summary)
        total_units = sum(s['total_units'] for s in summary)

        return jsonify({
            'summary': summary,
            'totals': {
                'services': total_services,
                'units': total_units,
                'date_range': f"{start_date} to {end_date}"
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ============= DASHBOARD OVERVIEW =============

@cpss_api.route('/api/cpss/dashboard', methods=['GET'])
@jwt_required
def get_dashboard_overview():
    """Get comprehensive dashboard data for CPSS user"""
    cpss_user_id = request.current_user.get('user_id')

    conn = sqlite3.connect(cpss_db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get active pods with participant counts
    cursor.execute('''
        SELECT p.*, COUNT(pp.id) as participant_count
        FROM cm_pods p
        LEFT JOIN pod_participants pp ON p.id = pp.pod_id AND pp.status = 'active'
        WHERE p.cpss_user_id = ? AND p.status = 'active'
        GROUP BY p.id
    ''', (cpss_user_id,))

    pods = [dict(row) for row in cursor.fetchall()]

    # Get today's sessions
    today = datetime.now().date()
    cursor.execute('''
        SELECT s.*, p.pod_name
        FROM group_sessions s
        JOIN cm_pods p ON s.pod_id = p.id
        WHERE p.cpss_user_id = ?
          AND DATE(s.scheduled_time) = ?
        ORDER BY s.scheduled_time
    ''', (cpss_user_id, today))

    today_sessions = [dict(row) for row in cursor.fetchall()]

    # Get recent drug tests needing review
    cursor.execute('''
        SELECT dt.*, pp.enrollment_id, e.patient_first_name, e.patient_last_name
        FROM drug_tests dt
        JOIN pod_participants pp ON dt.participant_id = pp.id
        JOIN cm_enrollments e ON pp.enrollment_id = e.id
        JOIN cm_pods p ON pp.pod_id = p.id
        WHERE p.cpss_user_id = ?
          AND dt.verified = 0
        ORDER BY dt.test_date DESC
        LIMIT 10
    ''', (cpss_user_id,))

    pending_reviews = [dict(row) for row in cursor.fetchall()]

    # Get upcoming milestones
    cursor.execute('''
        SELECT pp.*, e.patient_first_name, e.patient_last_name,
               CASE
                   WHEN pp.total_sessions_attended >= 4 AND pp.progress_phase = 'phase_1' THEN 'Ready for Phase 2'
                   WHEN pp.total_sessions_attended >= 8 AND pp.progress_phase = 'phase_2' THEN 'Ready for Phase 3'
                   WHEN pp.total_sessions_attended >= 12 AND pp.progress_phase = 'phase_3' THEN 'Ready for Graduation'
               END as milestone_status
        FROM pod_participants pp
        JOIN cm_enrollments e ON pp.enrollment_id = e.id
        JOIN cm_pods p ON pp.pod_id = p.id
        WHERE p.cpss_user_id = ?
          AND pp.status = 'active'
        HAVING milestone_status IS NOT NULL
    ''', (cpss_user_id,))

    upcoming_milestones = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'pods': pods,
        'today_sessions': today_sessions,
        'pending_reviews': pending_reviews,
        'upcoming_milestones': upcoming_milestones,
        'stats': {
            'total_active_participants': sum(p['participant_count'] for p in pods),
            'sessions_today': len(today_sessions),
            'pending_reviews': len(pending_reviews)
        }
    })