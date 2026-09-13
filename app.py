from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models import db, UsuarioModel, PlanoModel, TreinoModel, ItemExercicioModel, ExercicioBaseModel, TreinoBuilder
import os
from sqlalchemy import func


app = Flask(__name__)
app.secret_key = "fitlife_secret_key"

# Configuração do SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'fitlife.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

def inicializar_banco():
    db.create_all()
    
    # 1. Popula usuários iniciais se não existirem
    if not UsuarioModel.query.first():
        admin = UsuarioModel(nome="Guilherme Admin", email="admin@fitlife.com", perfil="ADMIN")
        admin.set_senha("1234")

        instrutor = UsuarioModel(nome="Carlos Instrutor", email="instrutor@fitlife.com", perfil="INSTRUTOR")
        instrutor.set_senha("1234")

        aluno = UsuarioModel(nome="João", email="aluno@fitlife.com", perfil="ALUNO", status_assinatura="ATIVO")
        aluno.set_senha("1234")
        
        db.session.add_all([admin, instrutor, aluno])
        
        p1 = PlanoModel(nome="Plano Mensal", valor=99.90)
        p2 = PlanoModel(nome="Plano Trimestral", valor=269.90)
        p3 = PlanoModel(nome="Plano Anual", valor=899.90)
        db.session.add_all([p1, p2, p3])
        
        db.session.commit()

    # 2. Popula base de exercícios pré-cadastrados
    if not ExercicioBaseModel.query.first():
        exercicios_padrao = [
            ExercicioBaseModel(nome="Supino Reto com Barra", grupo_muscular="Peito"),
            ExercicioBaseModel(nome="Supino Inclinado com Halteres", grupo_muscular="Peito"),
            ExercicioBaseModel(nome="Puxada Alta na Polia", grupo_muscular="Costas"),
            ExercicioBaseModel(nome="Remada Curvada", grupo_muscular="Costas"),
            ExercicioBaseModel(nome="Agachamento Livre", grupo_muscular="Pernas"),
            ExercicioBaseModel(nome="Leg Press 45°", grupo_muscular="Pernas"),
            ExercicioBaseModel(nome="Desenvolvimento com Halteres", grupo_muscular="Ombros"),
            ExercicioBaseModel(nome="Elevação Lateral", grupo_muscular="Ombros"),
            ExercicioBaseModel(nome="Rosca Direta", grupo_muscular="Bíceps"),
            ExercicioBaseModel(nome="Tríceps Corda", grupo_muscular="Tríceps")
        ]
        db.session.add_all(exercicios_padrao)
        db.session.commit()

with app.app_context():
    inicializar_banco()


# ==========================================
# ROTAS DA APLICAÇÃO
# ==========================================

@app.route("/", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        
        usuario = UsuarioModel.query.filter_by(email=email).first()
        if usuario and usuario.autenticar(senha):
            session["usuario_id"] = usuario.id
            session["email"] = usuario.email
            session["perfil"] = usuario.perfil
            
            if usuario.perfil == "ADMIN":
                return redirect(url_for("admin_dashboard"))
            elif usuario.perfil == "INSTRUTOR":
                return redirect(url_for("instrutor_dashboard"))
            else:
                return redirect(url_for("aluno_dashboard"))
        else:
            erro = "E-mail ou senha incorretos."

    return render_template("login.html", erro=erro)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    erro = None
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        
        if UsuarioModel.query.filter_by(email=email).first():
            erro = "Este e-mail já está cadastrado."
        else:
            novo_aluno = UsuarioModel(
                nome=nome,
                email=email,
                perfil="ALUNO",
                status_assinatura="PENDENTE"
            )
            novo_aluno.set_senha(senha)
            db.session.add(novo_aluno)
            db.session.commit()
            return redirect(url_for("login"))
            
    return render_template("registro.html", erro=erro)


@app.route("/instrutor", methods=["GET", "POST"])
def instrutor_dashboard():
    if session.get("perfil") != "INSTRUTOR":
        return redirect(url_for("login"))

    msg = None
    alunos = UsuarioModel.query.filter_by(perfil="ALUNO").all()
    exercicios_base = ExercicioBaseModel.query.order_by(ExercicioBaseModel.nome).all()

    email_aluno_sel = request.args.get("email_aluno") or (alunos[0].email if alunos else "")
    dia_semana_sel = request.args.get("dia_semana") or DIAS_SEMANA[0]
    
    aluno_obj = UsuarioModel.query.filter_by(email=email_aluno_sel).first()

    if request.method == "POST":
        email_aluno_sel = request.form.get("email_aluno")
        dia_semana_sel = request.form.get("dia_semana")
        aluno_obj = UsuarioModel.query.filter_by(email=email_aluno_sel).first()

        # Apaga o treino existente do dia
        treino_existente = TreinoModel.query.filter_by(aluno_id=aluno_obj.id, dia_semana=dia_semana_sel).first()
        if treino_existente:
            db.session.delete(treino_existente)

        # Se não for ação de apagar, constrói o treino com o Builder
        if not request.form.get("acao_apagar"):
            nomes = request.form.getlist("ex_nome[]")
            series = request.form.getlist("ex_series[]")
            reps = request.form.getlist("ex_reps[]")
            cargas = request.form.getlist("ex_carga[]")

            builder = TreinoBuilder(dia_semana_sel, aluno_obj.id)
            for i in range(len(nomes)):
                if nomes[i].strip():
                    builder.add_exercicio(
                        nome=nomes[i],
                        series=int(series[i]) if series[i] else 3,
                        repeticoes=int(reps[i]) if reps[i] else 10,
                        carga=float(cargas[i]) if cargas[i] else 0.0
                    )
            
            novo_treino = builder.build()
            if novo_treino.itens:
                db.session.add(novo_treino)
            msg = f"Treino de {dia_semana_sel} salvo com sucesso para {aluno_obj.nome}!"
        else:
            msg = f"Treino de {dia_semana_sel} removido com sucesso!"

        db.session.commit()

    treino_atual = TreinoModel.query.filter_by(aluno_id=aluno_obj.id, dia_semana=dia_semana_sel).first() if aluno_obj else None

    return render_template("instrutor.html", 
                           alunos=alunos, 
                           dias=DIAS_SEMANA, 
                           msg=msg, 
                           email_aluno_sel=email_aluno_sel, 
                           dia_semana_sel=dia_semana_sel, 
                           treino_atual=treino_atual,
                           exercicios_base=exercicios_base)


@app.route("/admin")
def admin_dashboard():
    if session.get("perfil") != "ADMIN":
        return redirect(url_for("login"))
    
    alunos = UsuarioModel.query.filter_by(perfil="ALUNO").all()
    planos = PlanoModel.query.all()

    # --- MÉTRICAS DE DADOS / SAAS ---
    total_alunos = len(alunos)
    alunos_ativos = sum(1 for a in alunos if a.status_assinatura == "ATIVO")
    alunos_pendentes = sum(1 for a in alunos if a.status_assinatura == "PENDENTE")
    alunos_cancelados = sum(1 for a in alunos if a.status_assinatura == "CANCELADO")

    # Faturamento Mensal Estimado (MRR) - considerando valor médio do plano ativo (R$ 99.90 base)
    mrr = alunos_ativos * 99.90
    
    # Taxa de Cancelamento (Churn Rate)
    churn_rate = round((alunos_cancelados / total_alunos * 100), 1) if total_alunos > 0 else 0.0

    # Dados para gráfico de Exercícios mais Prescritos (Top 5)
    top_exercicios = db.session.query(
        ItemExercicioModel.nome, 
        func.count(ItemExercicioModel.id).label('total')
    ).group_by(ItemExercicioModel.nome).order_by(func.count(ItemExercicioModel.id).desc()).limit(5).all()

    labels_ex = [item[0] for item in top_exercicios]
    data_ex = [item[1] for item in top_exercicios]

    return render_template(
        "admin.html", 
        alunos=alunos, 
        planos=planos,
        total_alunos=total_alunos,
        alunos_ativos=alunos_ativos,
        alunos_pendentes=alunos_pendentes,
        alunos_cancelados=alunos_cancelados,
        mrr=mrr,
        churn_rate=churn_rate,
        labels_ex=labels_ex,
        data_ex=data_ex
    )


@app.route("/aluno")
def aluno_dashboard():
    if session.get("perfil") != "ALUNO":
        return redirect(url_for("login"))
    aluno = UsuarioModel.query.get(session["usuario_id"])
    
    cronograma = {}
    for dia in DIAS_SEMANA:
        treino = TreinoModel.query.filter_by(aluno_id=aluno.id, dia_semana=dia).first()
        cronograma[dia] = treino.itens if treino else []

    return render_template("aluno.html", aluno=aluno, cronograma=cronograma)

@app.route("/aluno/pagamento", methods=["GET", "POST"])
def aluno_pagamento():
    if session.get("perfil") != "ALUNO":
        return redirect(url_for("login"))
        
    aluno = UsuarioModel.query.get(session["usuario_id"])
    planos = PlanoModel.query.all()

    if request.method == "POST":
        # Pega a instância concreta do Estado atual (PlanoPendente ou PlanoCancelado)
        estado_atual = aluno.get_estado_objeto()
        
        # Executa a transição de estado através do método do State
        msg = estado_atual.pagar(aluno)
        
        db.session.commit()
        return redirect(url_for("aluno_dashboard"))

    return render_template("pagamento.html", aluno=aluno, planos=planos)


@app.route("/aluno/cancelar-assinatura", methods=["GET", "POST"])
def cancelar_assinatura():
    if session.get("perfil") != "ALUNO":
        return redirect(url_for("login"))

    aluno = UsuarioModel.query.get(session["usuario_id"])
    
    # Transição de estado via Padrão State
    estado_atual = aluno.get_estado_objeto()
    estado_atual.cancelar(aluno)
    
    db.session.commit()
    return redirect(url_for("aluno_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================================
# ENDPOINTS DE API REST (JSON)
# ==========================================

@app.route("/api/v1/alunos", methods=["GET"])
def api_listar_alunos():
    """Retorna a lista de alunos e seus respectivos status no formato JSON."""
    alunos = UsuarioModel.query.filter_by(perfil="ALUNO").all()
    
    lista_alunos = [
        {
            "id": a.id,
            "nome": a.nome,
            "email": a.email,
            "status_assinatura": a.status_assinatura
        }
        for a in alunos
    ]
    
    return jsonify({
        "status": "sucesso",
        "total": len(lista_alunos),
        "dados": lista_alunos
    }), 200


@app.route("/api/v1/alunos/<int:aluno_id>/treinos", methods=["GET"])
def api_treinos_aluno(aluno_id):
    """Retorna o cronograma de treinos de um aluno específico via JSON."""
    aluno = UsuarioModel.query.get(aluno_id)
    
    if not aluno or aluno.perfil != "ALUNO":
        return jsonify({"status": "erro", "mensagem": "Aluno não encontrado"}), 404

    # Validação da regra do Padrão State
    estado = aluno.get_estado_objeto()
    if not estado.pode_acessar_treinos():
        return jsonify({
            "status": "bloqueado",
            "mensagem": f"Acesso negado. Assinatura com status '{aluno.status_assinatura}'."
        }), 403

    treinos = TreinoModel.query.filter_by(aluno_id=aluno.id).all()
    cronograma_json = {}

    for t in treinos:
        cronograma_json[t.dia_semana] = [
            {
                "exercicio": item.nome,
                "series": item.series,
                "repeticoes": item.repeticoes,
                "carga_kg": item.carga
            }
            for item in t.itens
        ]

    return jsonify({
        "status": "sucesso",
        "aluno": aluno.nome,
        "cronograma": cronograma_json
    }), 200

# Execução da aplicação
if __name__ == "__main__":
    app.run(debug=True)

