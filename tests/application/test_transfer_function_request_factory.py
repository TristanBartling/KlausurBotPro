"""Qt-independent tests for exact desktop request creation."""

from dataclasses import FrozenInstanceError, replace

import pytest

from klausurbotpro.application import (
    ParameterInputDraft,
    TransferFunctionInputDraft,
    TransferFunctionRequestFactory,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowService,
    WorkflowInputForm,
    render_solution_report_plaintext,
)


def _draft(
    *rows: ParameterInputDraft,
    form: WorkflowInputForm = WorkflowInputForm.COMMON,
) -> TransferFunctionInputDraft:
    return TransferFunctionInputDraft(
        form,
        "1/(T*s+1)",
        "1",
        "T*s+1",
        "s",
        rows,
        "transfer_function",
    )


def test_contracts_are_immutable_and_wrong_top_level_type_raises() -> None:
    draft = _draft()
    with pytest.raises(FrozenInstanceError):
        draft.variable_name = "z"  # type: ignore[misc]
    with pytest.raises(TypeError, match="TransferFunctionInputDraft"):
        TransferFunctionRequestFactory().create(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TransferFunctionWorkflowLimits"):
        TransferFunctionRequestFactory(object())  # type: ignore[arg-type]


def test_unassigned_parameter_is_allowed_and_sorted() -> None:
    result = TransferFunctionRequestFactory().create(
        _draft(
            ParameterInputDraft("T", "", ""),
            ParameterInputDraft("K", "", ""),
        )
    )

    assert result.succeeded
    assert result.request is not None
    assert result.request.allowed_parameter_names == ("K", "T")
    assert result.request.substitutions is None


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [
        ("2", "", (2, 1)),
        ("1", "2", (1, 2)),
        ("-2", "4", (-1, 2)),
        ("+6", "3", (2, 1)),
    ],
)
def test_exact_rational_assignments_are_canonical(
    numerator: str,
    denominator: str,
    expected: tuple[int, int],
) -> None:
    result = TransferFunctionRequestFactory().create(
        _draft(ParameterInputDraft("T", numerator, denominator))
    )

    assert result.request is not None
    assert result.request.substitutions is not None
    value = result.request.substitutions.assignments[0].value
    assert (value.numerator, value.denominator) == expected


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected_pole"),
    [("2", "", "-1/2"), ("1", "2", "-2")],
)
def test_exact_parameter_request_reaches_existing_workflow(
    numerator: str,
    denominator: str,
    expected_pole: str,
) -> None:
    creation = TransferFunctionRequestFactory().create(
        _draft(ParameterInputDraft("T", numerator, denominator))
    )
    assert creation.request is not None

    state = TransferFunctionWorkflowService().run(creation.request)
    report = TransferFunctionSolutionReportBuilder().build(state)
    plaintext = render_solution_report_plaintext(report)

    assert expected_pole in plaintext
    assert "Das System ist E/A-asymptotisch stabil." in plaintext


@pytest.mark.parametrize(
    ("row", "code"),
    [
        (ParameterInputDraft("", "1", ""), "value_without_parameter"),
        (
            ParameterInputDraft("T", "", "2"),
            "denominator_without_numerator",
        ),
        (ParameterInputDraft("T", "0.5", ""), "invalid_numerator"),
        (ParameterInputDraft("T", "1e3", ""), "invalid_numerator"),
        (ParameterInputDraft("T", "1", "0"), "invalid_denominator"),
        (ParameterInputDraft("T", "1", "-2"), "invalid_denominator"),
        (ParameterInputDraft("T", "1", "2.0"), "invalid_denominator"),
        (ParameterInputDraft("for", "", ""), "unsafe_identifier"),
        (ParameterInputDraft("unsafe-name", "", ""), "unsafe_identifier"),
        (ParameterInputDraft("s", "", ""), "variable_conflict"),
    ],
)
def test_invalid_parameter_rows_are_structured(
    row: ParameterInputDraft,
    code: str,
) -> None:
    result = TransferFunctionRequestFactory().create(_draft(row))

    assert not result.succeeded
    assert result.request is None
    assert result.errors[0].field == "parameter_rows"
    assert result.errors[0].code == code
    assert result.errors[0].row_index == 0


def test_duplicate_parameters_are_structured_without_partial_request() -> None:
    result = TransferFunctionRequestFactory().create(
        _draft(
            ParameterInputDraft("T", "", ""),
            ParameterInputDraft("T", "2", ""),
        )
    )

    assert result.request is None
    assert any(error.code == "duplicate_parameter" for error in result.errors)


def test_integer_digit_limit_is_checked_before_conversion() -> None:
    limits = TransferFunctionWorkflowLimits()
    oversized = "9" * (limits.parser.max_integer_digits + 1)
    result = TransferFunctionRequestFactory(limits).create(
        _draft(ParameterInputDraft("T", oversized, "1"))
    )

    assert result.request is None
    assert result.errors[0].code == "invalid_numerator"


def test_parameter_limit_is_structured() -> None:
    limits = TransferFunctionWorkflowLimits()
    rows = tuple(
        ParameterInputDraft(f"T{index}", "", "")
        for index in range(limits.parser.max_symbols)
    )

    result = TransferFunctionRequestFactory(limits).create(_draft(*rows))

    assert result.request is None
    assert any(
        error.code == "parameter_limit_exceeded" for error in result.errors
    )


@pytest.mark.parametrize(
    ("form", "expected_common", "expected_pair"),
    [
        (WorkflowInputForm.COMMON, "1/(T*s+1)", (None, None)),
        (WorkflowInputForm.SEPARATED, None, ("1", "T*s+1")),
    ],
)
def test_only_active_input_form_reaches_request(
    form: WorkflowInputForm,
    expected_common: str | None,
    expected_pair: tuple[str | None, str | None],
) -> None:
    result = TransferFunctionRequestFactory().create(_draft(form=form))

    assert result.request is not None
    assert result.request.common_expression_text == expected_common
    assert (
        result.request.numerator_expression_text,
        result.request.denominator_expression_text,
    ) == expected_pair


def test_empty_active_fields_and_variable_are_deterministic() -> None:
    draft = TransferFunctionInputDraft(
        WorkflowInputForm.SEPARATED,
        "kept",
        "",
        "",
        "unsafe-name",
    )

    result = TransferFunctionRequestFactory().create(draft)

    assert tuple(error.field for error in result.errors) == (
        "variable_name",
        "numerator_expression_text",
        "denominator_expression_text",
    )


@pytest.mark.parametrize(
    "variable_name",
    ("__s__", "__T", "T__", "class", "s mit Leerzeichen"),
)
def test_variable_uses_authoritative_safe_identifier_rule(
    variable_name: str,
) -> None:
    draft = replace(_draft(), variable_name=variable_name)

    result = TransferFunctionRequestFactory().create(draft)

    assert result.request is None
    assert result.errors[0].field == "variable_name"
    assert result.errors[0].code == "unsafe_identifier"


@pytest.mark.parametrize(
    "parameter_name",
    ("__K__", "__T", "K__", "class", " T "),
)
def test_parameter_uses_authoritative_safe_identifier_rule(
    parameter_name: str,
) -> None:
    result = TransferFunctionRequestFactory().create(
        _draft(ParameterInputDraft(parameter_name, "", ""))
    )

    assert result.request is None
    assert result.errors[0].field == "parameter_rows"
    assert result.errors[0].row_index == 0
    assert result.errors[0].code == "unsafe_identifier"


def test_safe_unicode_identifier_is_allowed() -> None:
    result = TransferFunctionRequestFactory().create(
        _draft(ParameterInputDraft("Trägheit", "", ""))
    )

    assert result.request is not None
    assert result.request.allowed_parameter_names == ("Trägheit",)


def test_effective_parameter_limit_includes_raw_and_root_contracts() -> None:
    default = TransferFunctionWorkflowLimits()
    raw_limited = replace(
        default,
        raw=replace(default.raw, max_parameters=1),
    )
    root_limited = replace(
        default,
        root_analysis=replace(default.root_analysis, max_parameters=1),
    )
    rows = (
        ParameterInputDraft("K", "", ""),
        ParameterInputDraft("T", "", ""),
    )

    for limits in (raw_limited, root_limited):
        result = TransferFunctionRequestFactory(limits).create(_draft(*rows))
        assert result.request is None
        assert result.errors[0].field == "parameter_rows"
        assert result.errors[0].code == "parameter_limit_exceeded"


def test_large_empty_row_tuple_is_rejected_without_iteration() -> None:
    rows = (ParameterInputDraft("", "", ""),) * 10_000

    result = TransferFunctionRequestFactory().create(_draft(*rows))

    assert result.request is None
    assert result.errors == (
        result.errors[0],
    )
    assert result.errors[0].field == "parameter_rows"
    assert result.errors[0].code == "parameter_limit_exceeded"


def test_empty_rows_within_limit_do_not_change_parameter_set() -> None:
    result = TransferFunctionRequestFactory().create(
        _draft(
            ParameterInputDraft("", "", ""),
            ParameterInputDraft("   ", "", ""),
        )
    )

    assert result.request is not None
    assert result.request.allowed_parameter_names == ()
    assert result.request.substitutions is None


@pytest.mark.parametrize(
    "limits",
    [
        replace(
            TransferFunctionWorkflowLimits(),
            parser=replace(
                TransferFunctionWorkflowLimits().parser,
                max_integer_digits=2,
            ),
        ),
        replace(
            TransferFunctionWorkflowLimits(),
            root_analysis=replace(
                TransferFunctionWorkflowLimits().root_analysis,
                max_substitution_integer_digits=2,
            ),
        ),
        replace(
            TransferFunctionWorkflowLimits(),
            stability_analysis=replace(
                TransferFunctionWorkflowLimits().stability_analysis,
                max_substitution_integer_digits=2,
            ),
        ),
    ],
)
def test_effective_integer_digit_limit_uses_all_relevant_contracts(
    limits: TransferFunctionWorkflowLimits,
) -> None:
    result = TransferFunctionRequestFactory(limits).create(
        _draft(ParameterInputDraft("T", "999", "1"))
    )

    assert result.request is None
    assert result.errors[0].code == "invalid_numerator"


def test_string_subclasses_and_non_tuple_rows_are_rejected() -> None:
    class StringSubclass(str):
        pass

    string_subclass = replace(
        _draft(),
        variable_name=StringSubclass("s"),
    )
    list_rows = replace(_draft(), parameter_rows=[])  # type: ignore[arg-type]
    subclass_row = _draft(
        ParameterInputDraft(StringSubclass("T"), "", "")
    )

    variable_result = TransferFunctionRequestFactory().create(string_subclass)
    rows_result = TransferFunctionRequestFactory().create(list_rows)
    row_result = TransferFunctionRequestFactory().create(subclass_row)

    assert variable_result.request is None
    assert variable_result.errors[0].field == "variable_name"
    assert variable_result.errors[0].code == "invalid_type"
    assert rows_result.request is None
    assert any(error.code == "invalid_rows" for error in rows_result.errors)
    assert row_result.request is None
    assert row_result.errors[0].field == "parameter_rows"
    assert row_result.errors[0].code == "invalid_type"


def test_parameter_row_is_fully_revalidated_and_bool_is_not_an_integer() -> None:
    row = ParameterInputDraft("T", True, "")  # type: ignore[arg-type]

    result = TransferFunctionRequestFactory().create(_draft(row))

    assert result.request is None
    assert result.errors[0].field == "parameter_rows"
    assert result.errors[0].code == "invalid_type"
