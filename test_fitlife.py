import pytest
from models import UsuarioModel, get_estado_objeto, ItemExercicioModel, TreinoModel

# ==========================================
# 1. TESTES DO PADRÃO STATE (Ciclo de Assinatura)
# ==========================================

def test_estado_pendente_bloqueia_acesso():
    """Garante que um aluno PENDENTE não pode acessar os treinos."""
    aluno = UsuarioModel(nome="Teste Pendente", email="pendente@fitlife.com", status_assinatura="PENDENTE")
    estado = aluno.get_estado_objeto()
    
    assert estado.get_nome() == "PENDENTE"
    assert estado.pode_acessar_treinos() is False

def test_estado_ativo_libera_acesso():
    """Garante que um aluno ATIVO pode acessar os treinos."""
    aluno = UsuarioModel(nome="Teste Ativo", email="ativo@fitlife.com", status_assinatura="ATIVO")
    estado = aluno.get_estado_objeto()
    
    assert estado.get_nome() == "ATIVO"
    assert estado.pode_acessar_treinos() is True

def test_transicao_pagamento_pendente_para_ativo():
    """Garante a transição PENDENTE -> ATIVO ao chamar o método pagar()."""
    aluno = UsuarioModel(nome="Teste Checkout", email="checkout@fitlife.com", status_assinatura="PENDENTE")
    estado_inicial = aluno.get_estado_objeto()
    
    # Simula a ação de pagamento no State
    msg = estado_inicial.pagar(aluno)
    
    assert aluno.status_assinatura == "ATIVO"
    assert aluno.get_estado_objeto().pode_acessar_treinos() is True

def test_transicao_cancelamento_ativo_para_cancelado():
    """Garante a transição ATIVO -> CANCELADO ao chamar o método cancelar()."""
    aluno = UsuarioModel(nome="Teste Cancelamento", email="cancelar@fitlife.com", status_assinatura="ATIVO")
    estado_inicial = aluno.get_estado_objeto()
    
    # Simula o cancelamento no State
    msg = estado_inicial.cancelar(aluno)
    
    assert aluno.status_assinatura == "CANCELADO"
    assert aluno.get_estado_objeto().pode_acessar_treinos() is False


# ==========================================
# 2. TESTES DO BUILDER / ESTRUTURA DE TREINOS
# ==========================================

def test_criacao_item_exercicio():
    """Testa a integridade da criação de um exercício prescrevível."""
    item = ItemExercicioModel(
        nome="Supino Reto",
        series=4,
        repeticoes=12,
        carga=30.0
    )
    
    assert item.nome == "Supino Reto"
    assert item.series == 4
    assert item.repeticoes == 12
    assert item.carga == 30.0