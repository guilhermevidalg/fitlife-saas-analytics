from models import db, UsuarioModel, PlanoModel, TreinoModel, ItemExercicioModel, TreinoBuilder

class FitLifeSystem:
    def autenticar(self, email, senha):
        usuario = UsuarioModel.query.filter_by(email=email).first()
        if usuario and usuario.autenticar(senha):
            return usuario
        return None

    def alternar_estado_aluno(self, email_aluno, novo_estado_str):
        aluno = UsuarioModel.query.filter_by(email=email_aluno, perfil="ALUNO").first()
        if aluno:
            aluno.status_assinatura = novo_estado_str
            db.session.commit()

    def adicionar_treino_aluno(self, email_aluno, dia_semana, lista_exercicios):
        aluno = UsuarioModel.query.filter_by(email=email_aluno, perfil="ALUNO").first()
        if aluno:
            # Apaga treino antigo do mesmo dia se existir
            treino_antigo = TreinoModel.query.filter_by(aluno_id=aluno.id, dia_semana=dia_semana).first()
            if treino_antigo:
                db.session.delete(treino_antigo)
                db.session.commit()

            # Cria novo treino via BUILDER
            builder = TreinoBuilder(dia_semana=dia_semana, aluno_id=aluno.id)
            for ex in lista_exercicios:
                builder.add_exercicio(ex['nome'], ex['series'], ex['reps'], ex['carga'])
            
            novo_treino = builder.build()
            if novo_treino.itens:
                db.session.add(novo_treino)
                db.session.commit()

    def remover_treino_aluno(self, email_aluno, dia_semana):
        aluno = UsuarioModel.query.filter_by(email=email_aluno, perfil="ALUNO").first()
        if aluno:
            treino = TreinoModel.query.filter_by(aluno_id=aluno.id, dia_semana=dia_semana).first()
            if treino:
                db.session.delete(treino)
                db.session.commit()

    def obter_treino_dia(self, aluno_id, dia_semana):
        return TreinoModel.query.filter_by(aluno_id=aluno_id, dia_semana=dia_semana).first()

    def obter_cronograma_completo(self, aluno_id):
        dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        cronograma = {}
        for d in dias:
            cronograma[d] = self.obter_treino_dia(aluno_id, d)
        return cronograma

sistema = FitLifeSystem()