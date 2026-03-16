from pydantic import BaseModel


class TriggerQualityControl(BaseModel):
    quality_control_setting_ids: list[int]
    start_date: str
    end_date: str
