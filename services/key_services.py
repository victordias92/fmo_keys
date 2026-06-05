from datetime import datetime

from database.key_repository import (
    update_key_use,
    get_key_by_id,
)

from services.excel_service import append_usage, get_last_user_key


DAY_MAP = {
    "Monday": "Segunda-feira",
    "Tuesday": "Terca-feira",
    "Wednesday": "Quarta-feira",
    "Thursday": "Quinta-feira",
    "Friday": "Sexta-feira",
    "Saturday": "Sabado",
    "Sunday": "Domingo",
}


def register_use(key_id: int, user: str, used: bool):

    now = datetime.now()

    used_date = now.strftime("%d/%m/%Y")
    used_time = now.strftime("%H:%M")

    used_day = DAY_MAP.get(
        now.strftime("%A"),
        now.strftime("%A"),
    )
    on_use = "Em uso"
    key = get_key_by_id(key_id)
    if used is True:
        get_last_user_key(key_id, used_date, used_time, used_day)
        return


    update_key_use(
        key_id,
        user,
        used_date,
        used_time,
        used_day,
       
    )

   

    append_usage(
        key["key_name"],
        user,
        used_date,
        used_time,
        used_day,
        on_use
        
    )