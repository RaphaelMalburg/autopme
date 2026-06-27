from app.advisor.service import build_commercial_brief


def test_commercial_brief_contains_follow_up_and_export():
    result = build_commercial_brief(
        {
            "business_name": "Clinica Exemplo",
            "niche": "dental",
            "extracted": {"website": "", "services": ["Limpeza"]},
            "extra": {"prices": "Limpeza: 50 EUR", "opening_hours": "Seg-Sex 9h-18h"},
            "roi": {
                "consultations_per_day": 20,
                "current_no_show_rate": 15,
                "target_no_show_rate": 5,
                "revenue_per_consultation": 60,
                "monthly_gain": 2640,
            },
        }
    )

    assert result["business_name"] == "Clinica Exemplo"
    assert result["roi_summary"]["monthly_gain"] == 2640
    assert result["follow_up"]["email_subject"]
    assert "AutoPME Demo" in result["export_markdown"]
