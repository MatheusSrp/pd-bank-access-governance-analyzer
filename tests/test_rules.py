"""Regras R01–R09 sobre dados com os cabeçalhos OFICIAIS (ver tests.helpers.mini_dataset)."""
import unittest
from datetime import date

from pdbank.rules import analyze, analyze_full
from tests.helpers import REF, mini, perm


def run(data, today=REF):
    return analyze(data, today)


def of(findings, rule=None, ftype=None):
    return [f for f in findings if (rule is None or f["rule_id"] == rule) and (ftype is None or f["finding_type"] == ftype)]


class ReferenceDateTests(unittest.TestCase):
    def test_reference_priority_param_then_dataset_info_then_today(self):
        d = mini(dataset_info=[{"campo": "data_referencia", "valor": "2026-11-05"}])
        out = analyze_full(d)
        self.assertEqual((out.reference_date, out.reference_source), ("2026-11-05", "dataset_info.data_referencia"))
        self.assertEqual(analyze_full(d, date(2026, 1, 1)).reference_date, "2026-01-01")
        self.assertEqual(analyze_full(mini()).reference_source, "data_atual")


class R01Tests(unittest.TestCase):
    def test_baseline_compatible_access_is_clean(self):
        self.assertEqual(of(run(mini()), "R01"), [])

    def test_permission_outside_baseline_uses_roles_resource_and_permission(self):
        d = mini(permissoes_atuais=[perm("P1", "U1", "RES1", "Read"), perm("P9", "U1", "RES2", "Admin", src="Direta"),
                                    perm("P8", "U1", "RES1", "Write")])
        f = of(run(d), "R01", "Excesso_de_Privilegio")
        self.assertEqual({(x["related_id"], x["severity"]) for x in f}, {("RES2", "critical"), ("RES1", "high")})
        self.assertEqual((f[0]["source_sheet"], f[0]["subject_id"]), ("permissoes_atuais", "U1"))
        self.assertIn("R01", f[0]["evidence"])   # papéis ativos do usuário aparecem na evidência

    def test_role_must_be_active_at_reference_date(self):
        d = mini()
        d["atribuicoes_papeis"][0]["end_date"] = "2026-01-01"
        self.assertEqual(len(of(run(d), "R01", "Excesso_de_Privilegio")), 1)

    def test_mode_broader_than_baseline_is_flagged_but_narrower_is_not(self):
        d = mini()
        d["rbac_baseline"][0]["expected_access_mode"] = "JIT"
        self.assertEqual(len(of(run(d), "R01", "Modo_de_Acesso_Divergente")), 1)
        d = mini()
        d["permissoes_atuais"][0]["access_mode"] = "JIT"
        d["permissoes_atuais"][0]["expiration_date"] = "2027-01-01"
        self.assertEqual(of(run(d), "R01"), [])

    def test_application_principals_are_not_compared_and_are_reported(self):
        d = mini(permissoes_atuais=[perm("A1", "APP01", "RES1", "Admin", ptype="Aplicacao")])
        out = analyze_full(d, REF)
        self.assertEqual(of(out.findings, "R01"), [])
        self.assertTrue(any("Aplicacao" in n for n in out.coverage["R01"]["notes"]))

    def test_unknown_principal_is_insufficient(self):
        f = of(run(mini(permissoes_atuais=[perm("P1", "U999", "RES1", "Read")])), "R01")
        self.assertEqual([x["status"] for x in f], ["insufficient_information"])

    def test_missing_sheets_mean_skipped_not_clean(self):
        for missing in ("rbac_baseline", "permissoes_atuais", "atribuicoes_papeis"):
            d = mini()
            d[missing] = []
            out = analyze_full(d, REF)
            self.assertFalse(out.coverage["R01"]["evaluated"], missing)


class R02Tests(unittest.TestCase):
    def test_role_based_conflict(self):
        d = mini()
        d["atribuicoes_papeis"] += [{"user_id": "U3", "role_id": "R11", "assignment_type": "Secundario", "start_date": "2026-04-01", "end_date": None, "__row": 9}]
        f = of(run(d), "R02")
        self.assertEqual((len(f), f[0]["subject_id"], f[0]["severity"]), (1, "U3", "critical"))
        self.assertIn("papéis atribuídos", f[0]["evidence"])

    def test_functional_conflict_derived_from_current_permission(self):
        d = mini(permissoes_atuais=[perm("P2", "U3", "RES2", "Approve"), perm("P3", "U3", "RES2", "Create")])
        f = of(run(d), "R02")
        self.assertEqual((len(f), f[0]["related_id"]), (1, "RES2"))
        self.assertIn("conflito funcional", f[0]["evidence"])

    def test_no_conflict_without_both_sides_and_no_rules_means_skipped(self):
        self.assertEqual(of(run(mini()), "R02"), [])
        d = mini()
        d["regras_sod"] = []
        self.assertFalse(analyze_full(d, REF).coverage["R02"]["evaluated"])


class R03Tests(unittest.TestCase):
    def asset(self, **k):
        return {"data_asset_id": "DA1", "resource_id": "RES1", "owner_id": "U1", "classification": "Confidencial",
                "contains_credentials": "Nao", **k}

    def test_complete_asset_is_clean(self):
        self.assertEqual(of(run(mini(ativos_dados=[self.asset()])), "R03"), [])

    def test_missing_owner_and_classification(self):
        f = of(run(mini(ativos_dados=[self.asset(owner_id=None), self.asset(data_asset_id="DA2", classification=None)])), "R03")
        self.assertEqual(sorted(x["finding_type"] for x in f), ["Classificacao_Ausente", "Proprietario_Ausente"])
        self.assertTrue(all(x["severity"] == "high" for x in f))

    def test_asset_less_restrictive_than_resource_and_credentials(self):
        f = of(run(mini(ativos_dados=[self.asset(resource_id="RES2"), self.asset(data_asset_id="DA2", contains_credentials="Sim")])), "R03")
        self.assertEqual([x["finding_type"] for x in f], ["Classificacao_Divergente"] * 2)

    def test_inactive_owner(self):
        self.assertEqual([x["finding_type"] for x in of(run(mini(ativos_dados=[self.asset(owner_id="U2")])), "R03")], ["Proprietario_Inativo"])


class R04Tests(unittest.TestCase):
    def share(self, **k):
        return {"sharing_id": "SH1", "data_asset_id": "DA1", "destination": "Email_Pessoal", "destination_approved": "Nao",
                "minimum_data_only": "Sim", "protected": "Sim", "recipient_type": "Terceiro", **k}

    def test_unapproved_destination_severity_follows_classification(self):
        assets = [{"data_asset_id": "DA1", "classification": "Restrito"}, {"data_asset_id": "DA2", "classification": "Interno"}]
        f = of(run(mini(ativos_dados=assets, eventos_compartilhamento=[self.share(), self.share(sharing_id="SH2", data_asset_id="DA2")])), "R04")
        self.assertEqual({(x["subject_id"], x["severity"]) for x in f}, {("SH1", "critical"), ("SH2", "medium")})

    def test_approved_destination_with_minimization_and_protection_is_clean(self):
        d = mini(ativos_dados=[{"data_asset_id": "DA1", "classification": "Restrito"}],
                 eventos_compartilhamento=[self.share(destination="SFTP_Aprovado", destination_approved="Sim")])
        self.assertEqual(of(run(d), "R04"), [])

    def test_approved_destination_without_protection_is_flagged(self):
        d = mini(ativos_dados=[{"data_asset_id": "DA1", "classification": "Interno"}],
                 eventos_compartilhamento=[self.share(destination_approved="Sim", protected="Nao")])
        self.assertEqual([x["finding_type"] for x in of(run(d), "R04")], ["Protecao_Insuficiente"])

    def test_unknown_asset_and_unreadable_approval_are_insufficient(self):
        d = mini(ativos_dados=[{"data_asset_id": "DA1", "classification": "Interno"}],
                 eventos_compartilhamento=[self.share(data_asset_id="DA9"), self.share(sharing_id="SH2", destination_approved="talvez")])
        self.assertEqual([x["status"] for x in of(run(d), "R04")], ["insufficient_information"] * 2)

    def test_incomplete_retention_policy_and_asset_without_policy(self):
        pol = {"retention_policy_id": "RP1", "data_asset_id": "DA1", "start_event": None, "retention_days": "0",
               "final_action": None, "evidence_required": None, "policy_status": "Politica_Incompleta"}
        ok = {**pol, "retention_policy_id": "RP2", "data_asset_id": "DA2", "start_event": "Criacao", "retention_days": "1095",
              "final_action": "Excluir", "evidence_required": "Log", "policy_status": "Hipotese_Educacional"}
        assets = [{"data_asset_id": f"DA{i}", "classification": "Interno", "owner_id": "U1"} for i in (1, 2, 3)]
        f = of(run(mini(ativos_dados=assets, politicas_retencao=[pol, ok])), "R04", "Retencao_Ausente")
        self.assertEqual(sorted(x["subject_id"] for x in f), ["DA1", "DA3"])


class R05R06Tests(unittest.TestCase):
    def ai(self, cid="AI1", action="Recomendar", impact="Baixo"):
        return {"ai_use_case_id": cid, "action_level": action, "impact_level": impact, "status": "Piloto"}

    def ctl(self, cid="AI1", **k):
        return {"ai_use_case_id": cid, "input_validation": "Sim", "output_validation": "Sim", "prompt_injection_protection": "Sim",
                "human_review": "Amostral", "logging": "Sim", "privilege_model": "Privilégio_Minimo", **k}

    def test_clean_case(self):
        out = run(mini(casos_uso_ia=[self.ai()], controles_ia=[self.ctl()]))
        self.assertEqual(of(out, "R05") + of(out, "R06"), [])

    def test_missing_prompt_protection_severity_follows_impact(self):
        out = run(mini(casos_uso_ia=[self.ai(impact="Alto")], controles_ia=[self.ctl(prompt_injection_protection="Nao")]))
        f = of(out, "R05", "Guardrail_Ausente")
        self.assertEqual((len(f), f[0]["severity"]), (1, "high"))

    def test_logging_only_required_from_medium_impact(self):
        low = run(mini(casos_uso_ia=[self.ai(impact="Baixo")], controles_ia=[self.ctl(logging="Nao")]))
        med = run(mini(casos_uso_ia=[self.ai(impact="Medio")], controles_ia=[self.ctl(logging="Nao")]))
        self.assertEqual((len(of(low, "R05")), len(of(med, "R05"))), (0, 1))

    def test_human_review_must_be_mandatory_for_high_impact(self):
        out = run(mini(casos_uso_ia=[self.ai(impact="Alto")], controles_ia=[self.ctl(human_review="Amostral")]))
        self.assertIn("obrigatória", of(out, "R05", "Guardrail_Ausente")[0]["evidence"])

    def test_privilege_model_excess(self):
        out = run(mini(casos_uso_ia=[self.ai()], controles_ia=[self.ctl(privilege_model="Acesso_Excessivo")]))
        self.assertEqual(len(of(out, "R05", "Acesso_Excessivo")), 1)

    def test_case_without_control_row_is_insufficient(self):
        self.assertEqual([x["status"] for x in of(run(mini(casos_uso_ia=[self.ai()])), "R05")], ["insufficient_information"])

    def test_unapproved_and_non_minimized_sources(self):
        d = mini(casos_uso_ia=[self.ai(impact="Alto")], controles_ia=[self.ctl(human_review="Obrigatoria")],
                 ativos_dados=[{"data_asset_id": "DA1", "classification": "Restrito", "contains_personal_data": "Sim"}],
                 fontes_dados_ia=[{"ai_use_case_id": "AI1", "data_asset_id": "DA1", "source_approved": "Nao", "minimized": "Nao", "access_level": "Read"}])
        out = run(d)
        self.assertEqual(sorted(x["finding_type"] for x in of(out, "R05")), ["Fonte_Nao_Aprovada", "Fonte_Sem_Minimizacao"])
        self.assertEqual(of(out, "R05", "Fonte_Nao_Aprovada")[0]["severity"], "critical")

    def test_autonomy_execute_critical_is_excessive_and_high_requires_mandatory_review(self):
        d = mini(casos_uso_ia=[self.ai("AI1", "Executar", "Critico"), self.ai("AI2", "Executar", "Alto"), self.ai("AI3", "Executar", "Alto")],
                 controles_ia=[self.ctl("AI1", human_review="Obrigatoria"), self.ctl("AI2", human_review="Obrigatoria"), self.ctl("AI3", human_review="Amostral")])
        f = of(run(d), "R06", "Agencia_Excessiva")
        self.assertEqual({(x["subject_id"], x["severity"]) for x in f}, {("AI1", "critical"), ("AI3", "high")})

    def test_shifted_columns_are_insufficient_not_guessed(self):
        f = of(run(mini(casos_uso_ia=[self.ai(action="Alto", impact="U016")], controles_ia=[self.ctl()])), "R06")
        self.assertEqual((f[0]["finding_type"], f[0]["status"]), ("Dado_Inconsistente", "insufficient_information"))

    def test_integrated_risk_requires_critical_credentials_and_excess(self):
        d = mini(casos_uso_ia=[self.ai("AI1", "Executar", "Critico")], controles_ia=[self.ctl(human_review="Obrigatoria", privilege_model="Acesso_Excessivo")],
                 ativos_dados=[{"data_asset_id": "DA3", "classification": "Restrito", "resource_id": "RES1", "contains_credentials": "Sim"}],
                 fontes_dados_ia=[{"ai_use_case_id": "AI1", "data_asset_id": "DA3", "source_approved": "Sim", "minimized": "Sim", "access_level": "Write"}])
        f = of(run(d), "R05", "Risco_Integrado")
        self.assertEqual((len(f), f[0]["related_id"], f[0]["category"]), (1, "DA3", "Integrado"))
        d["controles_ia"] = [self.ctl(human_review="Obrigatoria")]
        d["fontes_dados_ia"][0]["access_level"] = "Read"
        self.assertEqual(of(run(d), "R05", "Risco_Integrado"), [])


class R07R08R09Tests(unittest.TestCase):
    def test_r07_dismissed_user_with_permission_and_licence_not_violation(self):
        d = mini(permissoes_atuais=[perm("P1", "U2", "RES1", "Read"), perm("P2", "U2", "RES2", "Write", src="Direta")])
        f = of(run(d), "R07")
        self.assertEqual({(x["related_id"], x["severity"]) for x in f}, {("RES1", "high"), ("RES2", "critical")})
        d = mini(usuarios=[{"user_id": "U1", "status": "Licenca"}])
        out = analyze_full(d, REF)
        self.assertEqual(of(out.findings, "R07"), [])
        self.assertTrue(any("licença" in n for n in out.coverage["R07"]["notes"]))

    def test_r08_expired_temporary_and_jit_but_not_future_or_permanent(self):
        d = mini(permissoes_atuais=[perm("P1", "U1", "RES1", "Read", "Direta", "Temporario", "2026-06-30"),
                                    perm("P2", "U1", "RES1", "Read", "Via_Papel", "JIT", "2026-11-06"),
                                    perm("P3", "U1", "RES1", "Read", "Via_Papel", "JIT", "2026-11-04"),
                                    perm("P4", "U1", "RES1", "Read", "Via_Papel", "Temporario", None)])
        f = of(run(d), "R08")
        self.assertEqual(sorted((x["finding_type"], x["status"]) for x in f),
                         [("Acesso_Expirado", "non_compliant"), ("Acesso_Expirado", "non_compliant"), ("Expiracao_Indefinida", "insufficient_information")])

    def test_r09_pending_overdue_by_next_review_and_removal_not_executed(self):
        rv = lambda i, dec, nxt: {"review_id": i, "principal_id": "U1", "resource_id": "RES1", "review_date": "2026-01-01", "decision": dec,
                                  "next_review_date": nxt, "review_comment": "c"}
        d = mini(revisoes_acesso=[rv("A1", "Pendente", "2026-06-01"), rv("A2", "Pendente", "2027-01-01"), rv("A3", "Remover", "2027-01-01"),
                                  rv("A4", "Manter", "2026-01-01"), rv("A5", "Manter", "2027-01-01")])
        f = of(run(d), "R09")
        self.assertEqual(sorted(x["finding_type"] for x in f), ["Recertificacao_Vencida", "Remocao_Nao_Executada", "Revisao_Vencida"])


class ExceptionTests(unittest.TestCase):
    def exc(self, **k):
        e = {"exception_id": "EX1", "subject_id": "U1", "resource_or_asset_id": "RES2", "reason": "x", "approved_by": "U3",
             "expiration_date": "2026-12-01", "status": "Ativa", **k}
        return mini(permissoes_atuais=[perm("P9", "U1", "RES2", "Admin", src="Direta")], excecoes=[e])

    def r01(self, d, today=REF):
        return of(run(d, today), "R01", "Excesso_de_Privilegio")[0]

    def test_valid_exception_matches_subject_and_resource_and_keeps_severity(self):
        f = self.r01(self.exc())
        self.assertEqual((f["status"], f["exception_status"], f["severity"]), ("valid_exception", "valid", "critical"))
        self.assertIn("exceção aprovada", f["evidence"])

    def test_exception_for_other_resource_does_not_leak(self):
        self.assertEqual(self.r01(self.exc(resource_or_asset_id="RES1"))["exception_status"], "none")

    def test_expired_future_inactive_and_self_approved_do_not_suppress(self):
        self.assertEqual(self.r01(self.exc(), date(2027, 1, 1))["exception_status"], "expired")
        for k in ({"status": "Inativa"}, {"approved_by": None}, {"approved_by": "U1"}, {"expiration_date": "lixo"}):
            f = self.r01(self.exc(**k))
            self.assertEqual((f["status"], f["exception_status"]), ("non_compliant", "none"), k)

    def test_exception_without_target_applies_to_subject_of_asset_or_case(self):
        d = mini(casos_uso_ia=[{"ai_use_case_id": "AI3", "action_level": "Executar", "impact_level": "Critico"}],
                 controles_ia=[{"ai_use_case_id": "AI3", "input_validation": "Sim", "output_validation": "Sim", "prompt_injection_protection": "Sim",
                                "human_review": "Obrigatoria", "logging": "Sim", "privilege_model": "Privilégio_Minimo"}],
                 excecoes=[{"exception_id": "EX4", "subject_id": "AI3", "resource_or_asset_id": None, "approved_by": "U8",
                            "expiration_date": "2026-12-31", "status": "Ativa"}])
        f = of(run(d), "R06")
        self.assertEqual((f[0]["status"], f[0]["exception_status"]), ("valid_exception", "valid"))

    def test_unused_exceptions_are_reported_in_coverage(self):
        d = mini(excecoes=[{"exception_id": "EX9", "subject_id": "DA11", "resource_or_asset_id": None, "approved_by": "U8",
                            "expiration_date": "2026-12-31", "status": "Ativa"}])
        notes = analyze_full(d, REF).coverage["EXCEPTIONS"]["notes"]
        self.assertTrue(any("sem achado associado" in n and "DA11" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
