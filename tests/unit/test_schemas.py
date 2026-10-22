import pytest

from adsdata.ingestion.schemas import (
    AUDIT_COLUMNS,
    COMMON_COLUMNS,
    TABLE_SPECS,
    BigQueryType,
    Column,
    DataMode,
    TableSpec,
)

DATE = Column("date", BigQueryType.DATE, required=True)
CAMPAIGN = Column("campaign_id", BigQueryType.STRING, required=True)


@pytest.mark.parametrize("spec", TABLE_SPECS.values(), ids=TABLE_SPECS.keys())
class TestDeclaredSpecs:
    def test_share_common_and_audit_columns(self, spec):
        for column in (*COMMON_COLUMNS, *AUDIT_COLUMNS):
            assert spec.column(column.name) == column

    def test_are_partitioned_by_day_and_unique_per_campaign_and_day(self, spec):
        assert spec.partition_field == "date"
        assert spec.unique_key == ("date", "campaign_id")

    def test_have_a_cost_and_a_currency(self, spec):
        names = set(spec.column_names)

        assert names & {"cost_micros", "spend"}
        assert names & {"currency_code", "account_currency"}


def test_registry_is_read_only():
    with pytest.raises(TypeError):
        TABLE_SPECS["autre"] = TABLE_SPECS["meta_ads"]  # type: ignore[index]


def test_data_mode_accepts_only_known_modes():
    data_mode = AUDIT_COLUMNS[-1]

    assert data_mode.name == "data_mode"
    assert data_mode.allowed_values == {"real", "simulated"} == {m.value for m in DataMode}


@pytest.mark.parametrize(
    ("bq_type", "numeric"),
    [
        (BigQueryType.INT64, True),
        (BigQueryType.FLOAT64, True),
        (BigQueryType.STRING, False),
        (BigQueryType.DATE, False),
    ],
)
def test_numeric_columns(bq_type, numeric):
    assert Column("x", bq_type).is_numeric is numeric


def test_unknown_column_lookup_raises():
    with pytest.raises(KeyError, match="inconnue"):
        TABLE_SPECS["google_ads"].column("absente")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"columns": (DATE, CAMPAIGN, DATE)}, "en double"),
        ({"columns": (CAMPAIGN,), "unique_key": ("campaign_id",)}, "partition"),
        ({"columns": (Column("date", BigQueryType.STRING), CAMPAIGN)}, "partition"),
        ({"columns": (DATE, CAMPAIGN), "cluster_by": ("absente",)}, "clustering"),
        ({"columns": (DATE, CAMPAIGN), "cluster_by": ("date",) * 5}, "au plus"),
        ({"columns": (DATE, CAMPAIGN), "unique_key": ("absente",)}, "clé unique"),
    ],
)
def test_inconsistent_declarations_are_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        TableSpec(name="t", **kwargs)
