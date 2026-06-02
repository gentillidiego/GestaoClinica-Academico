import os
import random
import json
from datetime import datetime, timedelta
import sys

# Garante que o diretório pai (raiz) está no PYTHONPATH para importar 'database'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import execute_returning, execute, query

def generate_cpf():
    def calcula_digito(digs):
        s = 0
        peso = len(digs) + 1
        for d in digs:
            s += d * peso
            peso -= 1
        resto = 11 - (s % 11)
        return 0 if resto >= 10 else resto
    
    numeros = [random.randint(0, 9) for _ in range(9)]
    dv1 = calcula_digito(numeros)
    numeros.append(dv1)
    dv2 = calcula_digito(numeros)
    numeros.append(dv2)
    cpf = f"{numeros[0]}{numeros[1]}{numeros[2]}.{numeros[3]}{numeros[4]}{numeros[5]}.{numeros[6]}{numeros[7]}{numeros[8]}-{numeros[9]}{numeros[10]}"
    return cpf

NAMES_MALE = ["João", "José", "Carlos", "Roberto", "Felipe", "Marcos", "Lucas", "Mateus", "Thiago", "Arthur", "Gabriel", "Bruno", "Eduardo"]
NAMES_FEMALE = ["Maria", "Ana", "Juliana", "Patricia", "Fernanda", "Letícia", "Camila", "Beatriz", "Mariana", "Aline", "Larissa", "Laura", "Sofia"]
SURNAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins"]

def generate_name(gender):
    first = random.choice(NAMES_MALE if gender == "Masculino" else NAMES_FEMALE)
    return f"{first} {random.choice(SURNAMES)} {random.choice(SURNAMES)}"

def get_random_date_last_3_months():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    delta = end_date - start_date
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start_date + timedelta(seconds=random_second)

def populate_patients():
    aluno = query("SELECT id FROM users WHERE role = 'aluno' LIMIT 1", one=True)
    if not aluno:
        aluno = query("SELECT id FROM users LIMIT 1", one=True)
        
    professor = query("SELECT id FROM users WHERE role IN ('professor', 'admin') LIMIT 1", one=True)
    if not professor:
        professor = query("SELECT id FROM users LIMIT 1", one=True)
    
    if not aluno or not professor:
        print("Erro: É necessário ter ao menos um usuário cadastrado no banco.")
        return

    aluno_id = aluno['id']
    prof_id = professor['id']

    profiles = [
        "Saudável", "Saudável", "Saudável", "Saudável", "Saudável",
        "Cardiopata/Hipertenso", "Cardiopata/Hipertenso",
        "Idoso", "Idoso",
        "Diabético", "Diabético", "Diabético",
        "Criança", "Criança", "Criança"
    ]
    random.shuffle(profiles)

    fake_signature = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    for i, profile in enumerate(profiles):
        print(f"Gerando paciente {i+1}/15 - Perfil: {profile}")
        
        gender = random.choice(["Masculino", "Feminino"])
        nome = generate_name(gender)
        cpf = generate_cpf()
        rg = f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}"
        cns = f"7{random.randint(10000000000000, 99999999999999)}"
        celular = f"(82) 9{random.randint(8000, 9999)}-{random.randint(1000, 9999)}"
        email = f"{nome.split(' ')[0].lower()}.{nome.split(' ')[1].lower()}@exemplo.com"
        endereco = f"Rua {random.choice(SURNAMES)}, {random.randint(1, 999)} - Maceió, AL"

        # 1. Patient Data
        if profile == "Criança":
            idade = random.randint(4, 12)
            estado_civil = "Solteiro(a)"
            profissao = "Estudante"
        elif profile == "Idoso":
            idade = random.randint(65, 90)
            estado_civil = random.choice(["Casado(a)", "Viúvo(a)", "Divorciado(a)"])
            profissao = "Aposentado(a)"
        else:
            idade = random.randint(18, 60)
            estado_civil = random.choice(["Solteiro(a)", "Casado(a)", "Divorciado(a)"])
            profissao = random.choice(["Professor(a)", "Engenheiro(a)", "Comerciante", "Autônomo", "Médico(a)"])

        birth_date = (datetime.now() - timedelta(days=idade*365.25)).strftime("%Y-%m-%d")
        created_at = get_random_date_last_3_months()
        
        patient_data = (
            cns, nome, rg, cpf, profissao, endereco, "", "", "", email, gender, birth_date, "Brasileiro(a)", celular, estado_civil, "Não",
            generate_name(random.choice(["Masculino", "Feminino"])) if profile == "Criança" else "", 
            f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}" if profile == "Criança" else "",
            f"(82) 9{random.randint(8000, 9999)}-{random.randint(1000, 9999)}" if profile == "Criança" else "",
            f"responsavel@exemplo.com" if profile == "Criança" else ""
        )
        
        patient_id = execute_returning('''
            INSERT INTO patients (
                cns, nome, rg, cpf, profissao, endereco_residencial, endereco_comercial,
                cd_anterior, endereco_comercial_adicional, email, genero, data_nascimento,
                nacionalidade, celular, estado_civil, atendido_em, nome_responsavel,
                rg_responsavel, telefone_expedidor_responsavel, email_responsavel, criado_em
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', patient_data + (created_at,))

        # 2. TCLE
        execute('''
            INSERT INTO patient_tcle (patient_id, aluno_id, assinatura_base64, data_assinatura)
            VALUES (%s, %s, %s, %s)
        ''', (patient_id, aluno_id, fake_signature, created_at))

        # 3. Anamnesis
        anamnese_data = {
            "patient_id": patient_id, "queixa_principal": "", "sofre_doenca": "Não", "sofre_doenca_explica": "",
            "tomando_medicamento": "Não", "tomando_medicamento_explica": "", "pressao_arterial": "120/80",
            "fuma": "Não", "fuma_quantidade": "", "ingere_alcool": "Socialmente", "assinatura_base64": fake_signature,
            "data_anamnese": created_at
        }

        if profile == "Cardiopata/Hipertenso":
            anamnese_data["queixa_principal"] = "Dor ao mastigar"
            anamnese_data["sofre_doenca"] = "Sim"
            anamnese_data["sofre_doenca_explica"] = "Hipertensão arterial sistêmica"
            anamnese_data["tomando_medicamento"] = "Sim"
            anamnese_data["tomando_medicamento_explica"] = "Losartana 50mg"
            anamnese_data["pressao_arterial"] = "140/90"
        elif profile == "Diabético":
            anamnese_data["queixa_principal"] = "Gengiva sangrando muito ao escovar"
            anamnese_data["sofre_doenca"] = "Sim"
            anamnese_data["sofre_doenca_explica"] = "Diabetes tipo 2, última HbA1c 7.5%"
            anamnese_data["tomando_medicamento"] = "Sim"
            anamnese_data["tomando_medicamento_explica"] = "Metformina 850mg"
            anamnese_data["fuma"] = "Sim"
            anamnese_data["fuma_quantidade"] = "15"
        elif profile == "Idoso":
            anamnese_data["queixa_principal"] = "Prótese muito folgada"
            anamnese_data["sofre_doenca"] = "Sim"
            anamnese_data["sofre_doenca_explica"] = "Osteoporose"
            anamnese_data.update({"fez_cirurgia": "Sim", "fez_cirurgia_explica": "Cirurgia no joelho há 2 anos"})
        elif profile == "Criança":
            anamnese_data["queixa_principal"] = "Cárie no dente de trás"
            anamnese_data["ingere_alcool"] = "Não"
        else:
            anamnese_data["queixa_principal"] = "Limpeza de rotina e profilaxia"

        cols = ", ".join(anamnese_data.keys())
        placeholders = ", ".join(["%s"] * len(anamnese_data))
        anamnese_id = execute_returning(f'INSERT INTO anamnesis ({cols}) VALUES ({placeholders})', tuple(anamnese_data.values()))

        # 4. Exams
        # Físico
        exam_fisico_id = execute_returning('''
            INSERT INTO exams (anamnesis_id, patient_id, tipo, data_criacao, professor_id, data_validacao)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (anamnese_id, patient_id, 'fisico', created_at, prof_id, created_at))
        execute('''
            INSERT INTO exam_fisico (exam_id, estado_geral, pa_x, diagnostico_definitivo)
            VALUES (%s, %s, %s, %s)
        ''', (exam_fisico_id, 'Bom', anamnese_data["pressao_arterial"], 'Paciente apto para atendimento clínico odontológico.'))

        # Periograma (AAP 2018 engine support via JSON)
        exam_perio_id = execute_returning('''
            INSERT INTO exams (anamnesis_id, patient_id, tipo, data_criacao, professor_id, data_validacao)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (anamnese_id, patient_id, 'periograma', created_at, prof_id, created_at))
        
        if profile == "Diabético":
            perio_data = {
                "36": {"sitios": {"ps_36_mes": 6, "nci_36_mes": 4, "ss_36_mes": True}, "furca": 2, "mobilidade": 1},
                "46": {"sitios": {"ps_46_mes": 5, "nci_46_mes": 3, "ss_46_mes": True}, "mobilidade": 2}
            }
            diag_perio = "Periodontite Estágio IV, Localizada, Grau C"
        else:
            perio_data = {"11": {"sitios": {"ss_11_mes": True}}}
            diag_perio = "Gengivite Induzida por Biofilme Localizada"
            
        execute('''
            INSERT INTO exam_periograma (exam_id, fase, medicoes_data, diagnostico)
            VALUES (%s, %s, %s, %s)
        ''', (exam_perio_id, 'Inicial', json.dumps(perio_data), diag_perio))

        # Odontograma
        exam_odonto_id = execute_returning('''
            INSERT INTO exams (anamnesis_id, patient_id, tipo, data_criacao, professor_id, data_validacao)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (anamnese_id, patient_id, 'odontograma', created_at, prof_id, created_at))
        execute('''
            INSERT INTO exam_odontograma (exam_id, notas_dentes, observacoes)
            VALUES (%s, %s, %s)
        ''', (exam_odonto_id, '{"36": {"face_o": "Cárie", "face_m": "Restauração Deficiente"}}', 'Cáries detectadas e restaurações antigas mapeadas.'))

        # 5. Tratamento
        plano_id = execute_returning('''
            INSERT INTO planos_tratamento (patient_id, descricao, custo_estimado, status, criado_em)
            VALUES (%s, %s, %s, %s, %s)
        ''', (patient_id, f"Plano de Tratamento Integrado - {profile}", 0.0, 'Aprovado', created_at))
        
        procedimentos = [("36", "Restauração em Resina Composta (Oclusal)"), ("", "Raspagem Supragengival e Profilaxia Geral")]
        if profile == "Idoso":
            procedimentos = [("", "Moldagem e Confecção de Prótese Total Superior e Inferior"), ("", "Ajuste Oclusal")]
        elif profile == "Criança":
            procedimentos = [("74", "Restauração em Ionômero de Vidro"), ("", "Aplicação Tópica de Flúor"), ("84", "Selamento de Fóssulas e Fissuras")]
            
        proc_ids = []
        for dente, desc in procedimentos:
            pid = execute_returning('''
                INSERT INTO tratamento_procedimentos (patient_id, dente, descricao, professor_id, status, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (patient_id, dente, desc, prof_id, 'Concluido', created_at))
            proc_ids.append((pid, dente, desc))

        # 6. Atendimentos (Evolução) com as Três Assinaturas e Datas Corretas
        for pid, dente, desc in proc_ids:
            obs = f"Dente {dente}: {desc}" if dente else desc
            atendimento_data = created_at + timedelta(days=random.randint(1, 15))
            execute('''
                INSERT INTO atendimentos (
                    patient_id, data, observacoes, assinatura_paciente_base64, 
                    professor_id, status, created_by, aluno_executor_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                patient_id, atendimento_data.strftime('%Y-%m-%d %H:%M:%S'), 
                f"Procedimento realizado com sucesso, paciente cooperativo, sem intercorrências. {obs}", 
                fake_signature, prof_id, 'Concluido', aluno_id, aluno_id
            ))

    print("=== Concluído! 15 pacientes de demonstração inseridos com sucesso! ===")

if __name__ == "__main__":
    populate_patients()
