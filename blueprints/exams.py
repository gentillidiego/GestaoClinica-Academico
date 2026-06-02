from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from database import execute, execute_returning, query, execute_transaction
from werkzeug.security import check_password_hash
import json
import re

exams_bp = Blueprint('exams', __name__, url_prefix='/exams')

@exams_bp.route('/list/<int:anamnesis_id>')
@login_required
def list_exams(anamnesis_id):
    anamnesis = query("SELECT a.*, p.nome as patient_name FROM anamnesis a JOIN patients p ON a.patient_id = p.id WHERE a.id = %s", (anamnesis_id,), one=True)
    if not anamnesis:
        flash('Anamnese não encontrada.', 'danger')
        return redirect(url_for('anamnesis.search'))
    
    exams_list = query("SELECT * FROM exams WHERE anamnesis_id = %s ORDER BY data_criacao DESC", (anamnesis_id,))
    return render_template('exams/list.html', anamnesis=anamnesis, exams=exams_list)

@exams_bp.route('/check-anamnesis/<int:patient_id>')
@login_required
def check_anamnesis(patient_id):
    """Verifica se o paciente tem anamnese antes de criar exame."""
    anamnesis = query("SELECT id FROM anamnesis WHERE patient_id = %s ORDER BY id DESC LIMIT 1", (patient_id,), one=True)
    if not anamnesis:
        flash('Uma anamnese é necessária antes de realizar exames. Por favor, preencha o formulário abaixo.', 'warning')
        return redirect(url_for('anamnesis.form', patient_id=patient_id))
    
    return redirect(url_for('exams.select_type', anamnesis_id=anamnesis['id']))

@exams_bp.route('/create/<int:anamnesis_id>')
@login_required
def select_type(anamnesis_id):
    anamnesis = query("SELECT a.*, p.nome as patient_name FROM anamnesis a JOIN patients p ON a.patient_id = p.id WHERE a.id = %s", (anamnesis_id,), one=True)
    if not anamnesis:
        flash('Anamnese não encontrada.', 'danger')
        return redirect(url_for('anamnesis.search'))
        
    return render_template('exams/select_type.html', anamnesis=anamnesis)

# Placeholders para as rotas específicas que serão detalhadas pelo usuário
def _get_fisico_data():
    return (
        request.form.get('estado_geral'),
        request.form.get('peso_referido'),
        request.form.get('altura'),
        request.form.get('pulso'),
        request.form.get('freq_cardiaca'),
        request.form.get('pa_x'),
        request.form.get('lesao_presenca'),
        request.form.get('diagramas_pontos'),
        request.form.get('exame_extrabucal'),
        request.form.get('exame_intrabucal'),
        request.form.get('hipoteses_diagnosticas'),
        1 if 'imagem_periapical' in request.form else 0,
        1 if 'imagem_oclusal' in request.form else 0,
        1 if 'imagem_panoramica' in request.form else 0,
        1 if 'imagem_tomografia' in request.form else 0,
        request.form.get('imagem_outros'),
        request.form.get('imagem_resultado'),
        1 if 'hema_hemograma' in request.form else 0,
        1 if 'hema_coagulograma' in request.form else 0,
        1 if 'hema_glicemia' in request.form else 0,
        request.form.get('hema_outros'),
        request.form.get('hema_resultado'),
        1 if 'histo_incisional' in request.form else 0,
        1 if 'histo_excisional' in request.form else 0,
        request.form.get('diagnostico_definitivo')
    )

@exams_bp.route('/fisico/<int:anamnesis_id>', methods=['GET', 'POST'])
@exams_bp.route('/fisico/<int:anamnesis_id>/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def fisico(anamnesis_id, exam_id=None):
    anamnesis = query("SELECT a.*, p.nome as patient_name FROM anamnesis a JOIN patients p ON a.patient_id = p.id WHERE a.id = %s", (anamnesis_id,), one=True)
    if not anamnesis:
        flash('Anamnese não encontrada.', 'danger')
        return redirect(url_for('anamnesis.search'))

    exam_data = None
    if exam_id:
        exam_data = query("SELECT * FROM exam_fisico WHERE exam_id = %s", (exam_id,), one=True)

    if request.method == 'POST':
        # Se for edição
        if exam_id:
            execute("""
                UPDATE exam_fisico SET 
                    estado_geral=%s, peso_referido=%s, altura=%s, pulso=%s, freq_cardiaca=%s, pa_x=%s, 
                    lesao_presenca=%s, diagramas_pontos=%s, exame_extrabucal=%s, exame_intrabucal=%s, 
                    hipoteses_diagnosticas=%s, imagem_periapical=%s, imagem_oclusal=%s, 
                    imagem_panoramica=%s, imagem_tomografia=%s, imagem_outros=%s, imagem_resultado=%s, 
                    hema_hemograma=%s, hema_coagulograma=%s, hema_glicemia=%s, hema_outros=%s, 
                    hema_resultado=%s, histo_incisional=%s, histo_excisional=%s, diagnostico_definitivo=%s
                WHERE exam_id=%s
            """, (*_get_fisico_data(), exam_id))
            flash('Exame Físico atualizado com sucesso!', 'success')
        else:
            # Criar novo
            new_exam_id = execute_returning("INSERT INTO exams (anamnesis_id, patient_id, tipo) VALUES (%s, %s, %s)", 
                             (anamnesis_id, anamnesis['patient_id'], 'fisico'))
            
            execute("""
                INSERT INTO exam_fisico (
                    exam_id, estado_geral, peso_referido, altura, pulso, freq_cardiaca, pa_x, 
                    lesao_presenca, diagramas_pontos, exame_extrabucal, exame_intrabucal, 
                    hipoteses_diagnosticas, imagem_periapical, imagem_oclusal, 
                    imagem_panoramica, imagem_tomografia, imagem_outros, imagem_resultado, 
                    hema_hemograma, hema_coagulograma, hema_glicemia, hema_outros, 
                    hema_resultado, histo_incisional, histo_excisional, diagnostico_definitivo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_exam_id, *_get_fisico_data()))
            flash('Exame Físico salvo com sucesso!', 'success')
        
        return redirect(url_for('patients.view_patient', id=anamnesis['patient_id']))

    return render_template('exams/fisico.html', anamnesis=anamnesis, exam_data=exam_data)

@exams_bp.route('/odontograma/<int:anamnesis_id>', methods=['GET', 'POST'])
@exams_bp.route('/odontograma/<int:anamnesis_id>/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def odontograma(anamnesis_id, exam_id=None):
    anamnesis = query("SELECT a.*, p.nome as patient_name FROM anamnesis a JOIN patients p ON a.patient_id = p.id WHERE a.id = %s", (anamnesis_id,), one=True)
    if not anamnesis:
        flash('Anamnese não encontrada.', 'danger')
        return redirect(url_for('anamnesis.search'))

    exam_data = None
    if exam_id:
        exam_data = query("SELECT * FROM exam_odontograma WHERE exam_id = %s", (exam_id,), one=True)

    if request.method == 'POST':
        dentes_data = request.form.get('dentes_data')
        notas_dentes = request.form.get('notas_dentes')
        observacoes = request.form.get('observacoes')

        if exam_id:
            # Upsert logic: check if record exists in exam_odontograma
            exists = query("SELECT 1 FROM exam_odontograma WHERE exam_id = %s", (exam_id,), one=True)
            if exists:
                execute("UPDATE exam_odontograma SET dentes_data=%s, notas_dentes=%s, observacoes=%s WHERE exam_id=%s", 
                       (dentes_data, notas_dentes, observacoes, exam_id))
            else:
                execute("INSERT INTO exam_odontograma (exam_id, dentes_data, notas_dentes, observacoes) VALUES (%s, %s, %s, %s)", 
                       (exam_id, dentes_data, notas_dentes, observacoes))
            flash('Odontograma atualizado com sucesso!', 'success')
        else:
            # Criar novo
            new_exam_id = execute_returning("INSERT INTO exams (anamnesis_id, patient_id, tipo) VALUES (%s, %s, %s)", 
                             (anamnesis_id, anamnesis['patient_id'], 'odontograma'))
            
            execute("INSERT INTO exam_odontograma (exam_id, dentes_data, notas_dentes, observacoes) VALUES (%s, %s, %s, %s)", 
                   (new_exam_id, dentes_data, notas_dentes, observacoes))
            flash('Odontograma salvo com sucesso!', 'success')
            exam_id = new_exam_id
        
        return redirect(url_for('patients.view_patient', id=anamnesis['patient_id']))

    return render_template('exams/odontograma.html', anamnesis=anamnesis, exam_data=exam_data)

@exams_bp.route('/controle_placa/<int:anamnesis_id>', methods=['GET', 'POST'])
@exams_bp.route('/controle_placa/<int:anamnesis_id>/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def controle_placa(anamnesis_id, exam_id=None):
    anamnesis = query("SELECT a.*, p.nome as patient_name FROM anamnesis a JOIN patients p ON a.patient_id = p.id WHERE a.id = %s", (anamnesis_id,), one=True)
    if not anamnesis:
        flash('Anamnese não encontrada.', 'danger')
        return redirect(url_for('anamnesis.search'))

    exam_data = None
    if exam_id:
        exam_data = query("SELECT * FROM exam_controle_placa WHERE exam_id = %s", (exam_id,), one=True)

    if request.method == 'POST':
        data_faces = request.form.get('data_faces')
        num_dentes = request.form.get('num_dentes')
        num_faces_placa = request.form.get('num_faces_placa')
        indice_placa = request.form.get('indice_placa')
        psr_data = request.form.get('psr_data')
        condicao_periodontal = request.form.get('condicao_periodontal')

        if exam_id:
            execute("""
                UPDATE exam_controle_placa SET 
                    data_faces=%s, num_dentes=%s, num_faces_placa=%s, indice_placa=%s, 
                    psr_data=%s, condicao_periodontal=%s 
                WHERE exam_id=%s
            """, (data_faces, num_dentes, num_faces_placa, indice_placa, psr_data, condicao_periodontal, exam_id))
            flash('Controle de Placa atualizado!', 'success')
        else:
            new_exam_id = execute_returning("INSERT INTO exams (anamnesis_id, patient_id, tipo) VALUES (%s, %s, %s)", 
                             (anamnesis_id, anamnesis['patient_id'], 'controle_placa'))
            execute("""
                INSERT INTO exam_controle_placa (
                    exam_id, data_faces, num_dentes, num_faces_placa, indice_placa, 
                    psr_data, condicao_periodontal
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (new_exam_id, data_faces, num_dentes, num_faces_placa, indice_placa, psr_data, condicao_periodontal))
            flash('Controle de Placa salvo!', 'success')
        
        return redirect(url_for('patients.view_patient', id=anamnesis['patient_id']))

    return render_template('exams/controle_placa.html', anamnesis=anamnesis, exam_data=exam_data)

# Lógica clínica extraída para módulo de serviço dedicado
from services.periodontal_diagnosis import determinar_grau_periodontal, calculate_periograma_diagnosis

@exams_bp.route('/periograma/<int:anamnesis_id>', methods=['GET', 'POST'])
@exams_bp.route('/periograma/<int:anamnesis_id>/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def periograma(anamnesis_id, exam_id=None):
    anamnesis = query("SELECT a.*, p.nome as patient_name FROM anamnesis a JOIN patients p ON a.patient_id = p.id WHERE a.id = %s", (anamnesis_id,), one=True)
    if not anamnesis:
        flash('Anamnese não encontrada.', 'danger')
        return redirect(url_for('anamnesis.search'))

    exam_data = None
    if exam_id:
        exam_data = query("SELECT * FROM exam_periograma WHERE exam_id = %s", (exam_id,), one=True)

    if request.method == 'POST':
        fase = request.form.get('fase')
        medicoes_data = request.form.get('medicoes_data')
        diagnostico = request.form.get('diagnostico')

        if not medicoes_data:
            medicoes_data = "{}"
            
        ai_diag, ai_just = calculate_periograma_diagnosis(medicoes_data, anamnesis)
        ia_header = "DIAGNÓSTICO IA: "
        new_ia_text = f"{ia_header}{ai_diag}\nJUSTIFICATIVA: {ai_just}"

        if not diagnostico or diagnostico.strip() == "":
            diagnostico = new_ia_text
        else:
            # Se já existe um diagnóstico IA, vamos substituir pela versão atualizada
            if ia_header in diagnostico:
                # Tenta encontrar o bloco da IA (até o fim do texto ou próximo bloco)
                parts = re.split(f"({ia_header}.*)", diagnostico, flags=re.DOTALL)
                if len(parts) >= 2:
                    diagnostico = parts[0].strip() + ("\n\n" if parts[0].strip() else "") + new_ia_text
                else:
                    diagnostico = diagnostico + "\n\n" + new_ia_text
            else:
                # Apenas anexa se não encontrar o header
                diagnostico = diagnostico.strip() + "\n\n" + new_ia_text

        if exam_id:
            execute("UPDATE exam_periograma SET fase=%s, medicoes_data=%s, diagnostico=%s WHERE exam_id=%s", 
                   (fase, medicoes_data, diagnostico, exam_id))
            flash('Periograma atualizado!', 'success')
        else:
            new_exam_id = execute_returning("INSERT INTO exams (anamnesis_id, patient_id, tipo) VALUES (%s, %s, %s)", 
                             (anamnesis_id, anamnesis['patient_id'], 'periograma'))
            execute("INSERT INTO exam_periograma (exam_id, fase, medicoes_data, diagnostico) VALUES (%s, %s, %s, %s)", 
                   (new_exam_id, fase, medicoes_data, diagnostico))
            flash('Periograma salvo!', 'success')
        
        return redirect(url_for('patients.view_patient', id=anamnesis['patient_id']))

    return render_template('exams/periograma.html', anamnesis=dict(anamnesis), exam_data=exam_data)

@exams_bp.route('/imagem/<int:anamnesis_id>', methods=['GET', 'POST'])
@login_required
def imagem(anamnesis_id):
    return "Módulo de Exame de Imagem - Em breve."

@exams_bp.route('/delete/<int:patient_id>/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(patient_id, exam_id):
    username = request.form.get('prof_username')
    password = request.form.get('prof_password')
    tipo = request.form.get('tipo')
    
    # 1. Fetch user credentials
    user = query("SELECT id, password, role FROM users WHERE username = %s", (username,), one=True)
    if not user or not check_password_hash(user['password'], password):
        flash('Credenciais inválidas.', 'danger')
        return redirect(url_for('patients.view_patient', id=patient_id) + '#tab-exames')
        
    # 2. Check if user is admin or professor
    if user['role'] not in ['admin', 'professor']:
        flash('Apenas Administradores ou Professores podem excluir exames.', 'danger')
        return redirect(url_for('patients.view_patient', id=patient_id) + '#tab-exames')
        
    # 3. Perform deletion inside transaction
    try:
        child_table = None
        if tipo == 'fisico':
            child_table = 'exam_fisico'
        elif tipo == 'odontograma':
            child_table = 'exam_odontograma'
        elif tipo == 'controle_placa':
            child_table = 'exam_controle_placa'
        elif tipo == 'periograma':
            child_table = 'exam_periograma'
            
        queries = []
        if child_table:
            queries.append((f"DELETE FROM {child_table} WHERE exam_id = %s", (exam_id,)))
        queries.append(("DELETE FROM exams WHERE id = %s", (exam_id,)))
        
        execute_transaction(queries)
        flash('Exame excluído com sucesso.', 'success')
    except Exception as e:
        flash(f'Erro ao excluir exame: {str(e)}', 'danger')
        
    return redirect(url_for('patients.view_patient', id=patient_id) + '#tab-exames')
