from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from database import query
import datetime
from extensions import limiter

main_bp = Blueprint('main', __name__)

import time

@main_bp.route('/health')
@limiter.exempt
def health_check():
    """Endpoint de health check para monitoramento externo."""
    start = time.time()
    try:
        query("SELECT 1", one=True)
        db_ok = True
        db_latency = round((time.time() - start) * 1000, 2)
    except Exception as e:
        db_ok = False
        db_latency = -1

    status_code = 200 if db_ok else 503
    return jsonify({
        "status": "healthy" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "db_latency_ms": db_latency,
        "timestamp": time.time()
    }), status_code

@main_bp.route('/')
@login_required
def index():
    # Estatísticas básicas
    total_patients = query("SELECT COUNT(*) as count FROM patients", one=True)['count']
    
    # Pacientes no mês atual
    first_day_month = datetime.date.today().replace(day=1).strftime('%Y-%m-%d')
    patients_month = query("SELECT COUNT(*) as count FROM patients WHERE criado_em >= %s", (first_day_month,), one=True)['count']
    
    # Atendimentos hoje
    today = datetime.date.today().strftime('%Y-%m-%d')
    appointments_today = query("SELECT COUNT(*) as count FROM atendimentos WHERE date(data) = %s", (today,), one=True)['count']
    
    # Tratamentos pendentes
    pending_treatments = query("SELECT COUNT(*) as count FROM tratamento_procedimentos WHERE status = 'Pendente'", one=True)['count']

    # Últimos 5 pacientes cadastrados
    recent_patients = query(
        "SELECT id, nome, criado_em FROM patients ORDER BY id DESC LIMIT 5"
    )

    # Atendimentos aguardando assinatura do professor
    pending_signatures = query(
        "SELECT COUNT(*) as count FROM atendimentos WHERE professor_id IS NULL AND status != 'Concluido'",
        one=True
    )['count']

    stats = {
        'total_patients': total_patients,
        'patients_month': patients_month,
        'appointments_today': appointments_today,
        'pending_treatments': pending_treatments,
        'pending_signatures': pending_signatures,
    }
    
    return render_template('index.html', user=current_user, stats=stats, recent_patients=recent_patients)
