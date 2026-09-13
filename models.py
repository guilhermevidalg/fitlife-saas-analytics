from flask_sqlalchemy import SQLAlchemy
from abc import ABC, abstractmethod
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ==========================================
# PADRÃO STATE (Ciclo de Vida da Assinatura)
# ==========================================

class EstadoPlano(ABC):
    @abstractmethod
    def get_nome(self) -> str:
        pass

    @abstractmethod
    def pode_acessar_treinos(self) -> bool:
        pass

    @abstractmethod
    def pagar(self, usuario) -> str:
        pass

    @abstractmethod
    def cancelar(self, usuario) -> str:
        pass


class PlanoAtivo(EstadoPlano):
    def get_nome(self) -> str:
        return "ATIVO"

    def pode_acessar_treinos(self) -> bool:
        return True

    def pagar(self, usuario) -> str:
        return "Sua assinatura já está ativa e em dia!"

    def cancelar(self, usuario) -> str:
        usuario.status_assinatura = "CANCELADO"
        return "Sua assinatura foi cancelada com sucesso."


class PlanoPendente(EstadoPlano):
    def get_nome(self) -> str:
        return "PENDENTE"

    def pode_acessar_treinos(self) -> bool:
        return False

    def pagar(self, usuario) -> str:
        usuario.status_assinatura = "ATIVO"
        return "Pagamento confirmado! Sua assinatura foi ativada."

    def cancelar(self, usuario) -> str:
        usuario.status_assinatura = "CANCELADO"
        return "Cadastro cancelado antes da ativação."


class PlanoCancelado(EstadoPlano):
    def get_nome(self) -> str:
        return "CANCELADO"

    def pode_acessar_treinos(self) -> bool:
        return False

    def pagar(self, usuario) -> str:
        usuario.status_assinatura = "ATIVO"
        return "Reativação efetuada com sucesso! Seu plano está ativo novamente."

    def cancelar(self, usuario) -> str:
        return "Esta assinatura já se encontra cancelada."


def get_estado_objeto(nome_estado: str) -> EstadoPlano:
    if nome_estado == "PENDENTE":
        return PlanoPendente()
    elif nome_estado == "CANCELADO":
        return PlanoCancelado()
    return PlanoAtivo()


# ==========================================
# 2. MODELOS DO BANCO DE DADOS (SQLAlchemy)
# ==========================================

class UsuarioModel(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), nullable=False) # ADMIN, INSTRUTOR, ALUNO
    status_assinatura = db.Column(db.String(20), default="ATIVO")

    treinos = db.relationship('TreinoModel', backref='aluno', lazy=True, cascade="all, delete-orphan")

    def set_senha(self, senha_pura: str):
        self.senha = generate_password_hash(senha_pura)

    def autenticar(self, senha_pura: str) -> bool:
        return check_password_hash(self.senha, senha_pura)

    def get_estado_objeto(self) -> EstadoPlano:
        return get_estado_objeto(self.status_assinatura)

    def get_status_assinatura(self):
        return self.status_assinatura


class ExercicioBaseModel(db.Model):
    __tablename__ = 'exercicios_base'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    grupo_muscular = db.Column(db.String(50), nullable=True)


class PlanoModel(db.Model):
    __tablename__ = 'planos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)


class TreinoModel(db.Model):
    __tablename__ = 'treinos'
    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.String(20), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    itens = db.relationship('ItemExercicioModel', backref='treino', lazy=True, cascade="all, delete-orphan")


class ItemExercicioModel(db.Model):
    __tablename__ = 'itens_exercicio'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    series = db.Column(db.Integer, nullable=False)
    repeticoes = db.Column(db.Integer, nullable=False)
    carga = db.Column(db.Float, nullable=False)
    treino_id = db.Column(db.Integer, db.ForeignKey('treinos.id'), nullable=False)


# ==========================================
# 3. PADRÃO BUILDER (Construção de Treinos)
# ==========================================

class TreinoBuilder:
    def __init__(self, dia_semana: str, aluno_id: int):
        self.dia_semana = dia_semana
        self.aluno_id = aluno_id
        self.itens = []

    def add_exercicio(self, nome: str, series: int, repeticoes: int, carga: float):
        if nome and nome.strip():
            item = ItemExercicioModel(
                nome=nome.strip(),
                series=series,
                repeticoes=repeticoes,
                carga=carga
            )
            self.itens.append(item)
        return self

    def build(self) -> TreinoModel:
        treino = TreinoModel(dia_semana=self.dia_semana, aluno_id=self.aluno_id)
        treino.itens = self.itens
        return treino