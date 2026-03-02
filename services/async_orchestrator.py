
import asyncio
from services.orchestrator import run_pipeline
from services.system_risk_engine import compute_system_risk
from services.predictive_engine import predict_failure_probability
from datetime import datetime

async def async_diagnosis(vehicle_id, symptoms=None, chat_input=None, obd_codes=None):

    # Run base diagnosis in thread
    loop = asyncio.get_event_loop()
    diagnosis_result = await loop.run_in_executor(
        None,
        lambda: run_pipeline(vehicle_id, symptoms, chat_input, obd_codes)
    )

    if not diagnosis_result:
        return None

    related_systems = diagnosis_result.get("related_systems", [])
    primary_system = related_systems[0] if related_systems else "default"

    # Parallel tasks
    risk_task = loop.run_in_executor(
        None,
        lambda: compute_system_risk(primary_system, datetime.utcnow())
    )

    predictive_task = loop.run_in_executor(
        None,
        lambda: predict_failure_probability(primary_system, datetime.utcnow())
    )

    projected_risk, failure_probability = await asyncio.gather(
        risk_task,
        predictive_task
    )

    diagnosis_result["async_projected_risk"] = projected_risk
    diagnosis_result["async_failure_probability"] = failure_probability

    return diagnosis_result
