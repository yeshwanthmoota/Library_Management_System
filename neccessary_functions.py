from datetime import datetime
import pytz

def get_current_time():
    timeZ_Kl = pytz.timezone('Asia/Kolkata')
    dt_Kl = datetime.now(timeZ_Kl)
    return (dt_Kl.strftime('%Y-%m-%d %H:%M:%S'))