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
