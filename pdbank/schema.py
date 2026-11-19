"""Catálogo de abas e aliases de campos.

Os nomes das 20 abas e os cabeçalhos de campo foram CONFIRMADOS contra o dataset oficial
(PD_Bank_Analyzer_Dataset_Completo_Alunos, versão 2.0) na v0.4.0. Ajustes futuros de schema
ficam neste arquivo (e em ``tests/test_values_schema.py``).
"""
from __future__ import annotations

import re

from .values import is_blank, normalize

OFFICIAL_SHEETS = (
    "dataset_info", "usuarios", "aplicacoes", "recursos", "catalogo_papeis",
    "atribuicoes_papeis", "rbac_baseline", "permissoes_atuais", "regras_sod",
    "revisoes_acesso", "ativos_dados", "campos_dados", "eventos_compartilhamento",
    "politicas_retencao", "casos_uso_ia", "fontes_dados_ia", "controles_ia",
    "excecoes", "casos_teste_publicos", "dicionario_de_dados",
)

# nome interno -> nomes de aba aceitos (já normalizados). Cada alias pertence a UMA só chave.
SHEET_ALIASES = {
    "info": ("dataset_info",),
    "users": ("users", "user", "usuarios", "usuario"),
    "applications": ("applications", "aplicacoes", "aplicacao"),
    "resources": ("resources", "recursos", "recurso"),
    "roles": ("roles", "catalogo_papeis", "papeis"),
    "role_assignments": ("role_assignments", "atribuicoes_papeis"),
    "baseline": ("access_baseline", "baseline", "baseline_permissoes", "permissoes_baseline", "rbac_baseline"),
    "assignments": ("access_assignments", "atribuicoes_acesso", "permissoes_atuais", "current_access", "accesses"),
    "sod": ("sod_rules", "regras_sod", "segregacao_funcoes"),
    "reviews": ("access_reviews", "revisoes_acesso"),
    "assets": ("data_assets", "ativos_dados", "ativos"),
    "data_fields": ("data_fields", "campos_dados"),
    "sharing": ("sharing_events", "eventos_compartilhamento", "compartilhamentos"),
    "retention": ("retention_policies", "politicas_retencao", "retencao"),
    "ai": ("ai_use_cases", "casos_uso_ia", "casos_ia"),
    "ai_sources": ("ai_data_sources", "fontes_dados_ia"),
    "ai_controls": ("ai_controls", "controles_ia"),
    "exceptions": ("exceptions", "excecoes"),
    "public_test_cases": ("public_test_cases", "casos_teste_publicos"),
    "data_dictionary": ("data_dictionary", "dicionario_de_dados"),
}
ALIAS_TO_CANONICAL = {a: k for k, aliases in SHEET_ALIASES.items() for a in aliases}

# nome interno -> nomes de campo aceitos (já normalizados). Cada alias pertence a UM só grupo (testado).
# Os cabeçalhos REAIS do dataset oficial (PD_Bank_Analyzer_Dataset_Completo_Alunos, v2.0) vêm primeiro em
# cada grupo; os demais são apelidos tolerantes, mantidos por compatibilidade com planilhas de outras origens.
FIELD_ALIASES = {
    # --- identidades e papéis
    "subject_id": ("user_id", "principal_id", "subject_id", "usuario_id", "id_usuario", "usuario"),
    "role_id": ("role_id", "papel_id", "id_papel", "papel_primario_id"),
    "role_name": ("role_name", "papel_primario", "nome_papel"),
    "privileged_role": ("privileged_role", "papel_privilegiado"),
    "area": ("area", "business_area"),
    "criticality": ("criticality", "criticidade"),
    "assignment_type": ("assignment_type", "tipo_atribuicao"),
    "manager_id": ("manager_id", "gestor_id"),
    # --- permissões
    "perm_record_id": ("permission_id", "permissao_id"),
    "permission": ("permission", "allowed_permission", "permissao", "privilege", "privilegio"),
    "principal_type": ("principal_type", "tipo_principal"),
    "resource_id": ("resource_id", "recurso_id", "id_recurso"),
    "assignment_source": ("assignment_source", "origem_atribuicao"),
    "access_mode": ("access_mode", "modo_acesso"),
    "expected_access_mode": ("expected_access_mode", "modo_acesso_esperado"),
    "valid_from": ("start_date", "grant_date", "valid_from", "data_inicio", "inicio_vigencia"),
    "valid_until": ("end_date", "expiration_date", "valid_until", "expires_at", "data_expiracao", "data_fim",
                    "data_vencimento", "fim_vigencia"),
    "last_used": ("last_used_date", "ultimo_uso"),
    "justification": ("business_justification", "justificativa"),
    # --- SoD
    "rule_id": ("rule_id", "regra_id", "regra"),
    "role_a": ("role_a", "papel_a", "role_id_a", "papel_id_a"),
    "role_b": ("role_b", "papel_b", "role_id_b", "papel_id_b"),
    "severity": ("severity", "severidade"),
    # --- revisões
    "review_id": ("review_id", "id_revisao"),
    "decision": ("decision", "decisao"),
    "next_review": ("next_review_date", "proxima_revisao"),
    "review_date": ("review_date", "data_revisao"),
    "reviewer_id": ("reviewer_id", "revisor_id"),
    "comment": ("review_comment", "comentario"),
    # --- dados
    "asset_id": ("data_asset_id", "asset_id", "ativo_id", "id_ativo"),
    "asset_name": ("asset_name", "nome_ativo"),
    "classification": ("classification", "classificacao", "data_classification"),
    "owner": ("owner_id", "owner", "proprietario", "responsavel"),
    "has_personal": ("contains_personal_data",),
    "has_financial": ("contains_financial_data",),
    "has_credentials": ("contains_credentials",),
    "sharing_id": ("sharing_id", "event_id", "id_evento"),
    "destination": ("destination", "destino"),
    "destination_approved": ("destination_approved", "destino_aprovado"),
    "minimum_data_only": ("minimum_data_only", "somente_dados_minimos"),
    "protected": ("protected", "protegido"),
    "recipient_type": ("recipient_type", "tipo_destinatario"),
    "requested_by": ("requested_by", "solicitante_id"),
    "policy_id": ("retention_policy_id", "policy_id", "id_politica"),
    "retention_days": ("retention_days", "dias_retencao"),
    "start_event": ("start_event", "evento_inicio"),
    "final_action": ("final_action", "acao_final"),
    "evidence_required": ("evidence_required", "evidencia_exigida"),
    "policy_status": ("policy_status", "status_politica"),
    # --- IA
    "case_id": ("ai_use_case_id", "use_case_id", "caso_uso_id", "case_id", "id_caso_uso"),
    "application_id": ("application_id", "aplicacao_id"),
    "action_level": ("action_level", "nivel_acao"),
    "impact_level": ("impact_level", "nivel_impacto"),
    "source_approved": ("source_approved", "fonte_aprovada"),
    "minimized": ("minimized", "minimizado"),
    "access_level": ("access_level", "nivel_acesso"),
    "input_validation": ("input_validation",),
    "output_validation": ("output_validation",),
    "prompt_protection": ("prompt_injection_protection",),
    "human_review": ("human_review", "revisao_humana"),
    "logging": ("logging", "log_ativo"),
    "privilege_model": ("privilege_model", "modelo_privilegio"),
    # --- exceções
    "exception_id": ("exception_id", "id_excecao"),
    "exception_target": ("resource_or_asset_id", "recurso_ou_ativo_id"),
    "approved_by": ("approved_by", "aprovado_por"),
    # --- genéricos
    "status": ("status", "situacao", "state"),
    "name": ("name", "nome", "nome_ficticio"),
    # --- casos de teste públicos
    "test_case_id": ("test_case_id",),
    "domain": ("domain", "dominio"),
    "related_id": ("related_id",),
    "expected_priority": ("expected_priority",),
    "expected_decision": ("expected_decision",),
    "expected_category": ("expected_category",),
    "scenario": ("scenario", "cenario"),
}
_FIELD_TO_GROUP = {}
for _group, _names in FIELD_ALIASES.items():
    for _n in _names:
        if _n in _FIELD_TO_GROUP:
            raise RuntimeError(f"alias de campo duplicado: {_n!r} em {_FIELD_TO_GROUP[_n]!r} e {_group!r}")
        _FIELD_TO_GROUP[_n] = _group

# Colunas oficiais que existem no dataset mas são apenas descritivas (nenhuma regra as consome hoje).
INFORMATIONAL_FIELDS = frozenset({
    "campo", "valor", "arquivo", "descricao", "data_admissao", "application_name", "environment", "resource_name",
    "resource_type", "rationale", "purpose", "sharing_date", "reason", "exception_condition", "field_id", "field_name",
    "data_category", "sensitive", "direct_identifier"})

# Campos que cada regra precisa para funcionar (usado só para AVISOS de cobertura).
REQUIRED_FIELDS = {
    "assignments": (("subject_id",), ("permission",), ("resource_id",)),
    "baseline": (("role_id",), ("resource_id",), ("permission",)),
    "role_assignments": (("subject_id",), ("role_id",)),
    "sod": (("role_a",), ("role_b",)),
    "assets": (("asset_id",), ("classification",), ("owner",)),
    "reviews": (("subject_id",), ("decision",)),
    "users": (("subject_id",), ("status",)),
    "sharing": (("asset_id",), ("destination_approved",)),
    "retention": (("asset_id",), ("retention_days",)),
    "ai": (("case_id",), ("action_level",), ("impact_level",)),
    "ai_sources": (("case_id",), ("asset_id",)),
    "ai_controls": (("case_id",),),
    "exceptions": (("subject_id",), ("valid_until",), ("status",)),
}


_DUP_SUFFIX = re.compile(r"^(.+?)__\d+$")


def base_sheet_key(name: object) -> str:
    """Chave normalizada da aba, removendo o sufixo '__N' que o importador acrescenta a duplicatas."""
    raw = str(name if name is not None else "")
    m = _DUP_SUFFIX.match(raw)
    return normalize(m.group(1) if m else raw)


def canonical_sheet(name: object) -> str:
    key = base_sheet_key(name)
    return ALIAS_TO_CANONICAL.get(key, key)


def is_known_sheet(name: object) -> bool:
    return base_sheet_key(name) in ALIAS_TO_CANONICAL


def get(row: dict, *keys: str, default=None):
    """Primeiro valor não vazio. Cada ``key`` é um grupo de FIELD_ALIASES (expande aliases)
    ou um nome literal de coluna. Nunca mistura grupos: 'user_id' não devolve 'asset_id'."""
    for key in keys:
        names = FIELD_ALIASES.get(key) or (key,)
        for name in names:
            value = row.get(normalize(name))
            if value is not None and not is_blank(value):
                return value
    return default


def has_column(rows: list, *keys: str) -> bool:
    return any(get(r, *keys) is not None for r in rows if isinstance(r, dict))


# Taxonomia de classificação do dataset oficial (valores distintos de ``ativos_dados`` e ``recursos``),
# do menos ao mais restritivo. Valores fora da lista são tratados como desconhecidos (nunca como "público").
CLASSIFICATION_ORDER = {"publico": 0, "interno": 1, "confidencial": 2, "restrito": 3}
RESTRICTED_CLASSIFICATIONS = frozenset({"restrito", "confidencial"})
