from mananze_os.workforce_planner import WorkforcePlanner


def test_workforce_planner_includes_required_skills() -> None:
    workforce = WorkforcePlanner().plan(
        "wo-skills",
        "help a dentist increase patient appointments",
    )

    appointment_role = next(
        role
        for role in workforce.roles
        if role.capability_id == "appointment_booking"
    )

    assert appointment_role.skill_ids == (
        "appointment_booking:scheduling",
    )

    marketing_role = next(
        role
        for role in workforce.roles
        if role.capability_id == "marketing"
    )

    assert marketing_role.skill_ids == (
        "marketing:campaign_planning",
        "marketing:content_creation",
    )

    sales_role = next(
        role
        for role in workforce.roles
        if role.capability_id == "sales"
    )

    assert sales_role.skill_ids == (
        "sales:lead_qualification",
        "sales:follow_up",
    )

    reporting_role = next(
        role
        for role in workforce.roles
        if role.capability_id == "reporting"
    )

    assert reporting_role.skill_ids == (
        "reporting:business_reporting",
    )
