import re
from dataclasses import dataclass
from random import randint

from croniter import croniter
from fastapi import HTTPException

from constants import CustomJobType, IngestType
from models import CustomJobParamSpec, CustomJobSpec

MAX_RANDOM_JITTER_SECONDS = 30

# digits and * , - / only, i.e. the subset every cron implementation agrees on
_FIELD_RE = re.compile(r"^[0-9*,/\-]+$")


@dataclass(frozen=True)
class JobDefinition:
    job_type: CustomJobType
    label: str
    description: str
    ingest_types: tuple[IngestType, ...]
    params: tuple[CustomJobParamSpec, ...] = ()


CATALOG: dict[CustomJobType, JobDefinition] = {
    d.job_type: d
    for d in (
        JobDefinition(
            CustomJobType.SYNC_THING,
            "Additional sync",
            "Runs the regular sync of this ingest an additional time.",
            (IngestType.EXTERNAL_API, IngestType.EXTERNAL_SFTP),
        ),
        JobDefinition(
            CustomJobType.RESYNC_THING,
            "Resync",
            "Re-fetches the last N days from the external API, independent of the sync interval.",
            (IngestType.EXTERNAL_API,),
            (
                CustomJobParamSpec(
                    name="days",
                    label="Look-back window (days)",
                    type="int",
                    default=7,
                    minimum=1,
                    maximum=365,
                ),
            ),
        ),
    )
}


def available_jobs(ingest_type: str) -> list[CustomJobSpec]:
    return [
        CustomJobSpec(
            job_type=d.job_type,
            label=d.label,
            description=d.description,
            params=list(d.params),
        )
        for d in CATALOG.values()
        if ingest_type in d.ingest_types
    ]


def validate_job_type(job_type: CustomJobType, ingest_type: str) -> JobDefinition:
    definition = CATALOG.get(job_type)
    if definition is None or ingest_type not in definition.ingest_types:
        raise HTTPException(
            status_code=422,
            detail=f"Job type '{job_type.value}' is not available for this ingest",
        )
    return definition


def validate_params(definition: JobDefinition, params: dict) -> dict:
    """Return the params restricted to the definition, defaults filled in."""
    unknown = set(params) - {p.name for p in definition.params}
    if unknown:
        raise HTTPException(
            status_code=422, detail=f"Unknown parameters: {sorted(unknown)}"
        )
    result = {}
    for spec in definition.params:
        value = params.get(spec.name, spec.default)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not spec.minimum <= value <= spec.maximum
        ):
            raise HTTPException(
                status_code=422,
                detail=f"{spec.name} must be an integer in {spec.minimum}..{spec.maximum}",
            )
        result[spec.name] = value
    return result


def normalize_cron_expression(expression: str) -> str:
    fields = expression.split()
    if (
        len(fields) != 5
        or not all(_FIELD_RE.match(f) for f in fields)
        or not croniter.is_valid(" ".join(fields))
    ):
        raise HTTPException(
            status_code=422,
            detail="cron_expression must be 5 fields of numbers, '*', ',', '-' and '/'",
        )
    return " ".join(fields)


def random_jitter() -> int:
    return randint(0, MAX_RANDOM_JITTER_SECONDS)
