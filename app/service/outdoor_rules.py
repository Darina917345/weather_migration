"Бізнес-правило: «Чи варто виходити на вулицю?» (за даними про опади)"

# Порогові значення. Змінюєте тут — змінюється правило для нових даних.
PRECIP_MAX_MM = 0.5   # від 0.5 мм опадів уже мокро
HUMIDITY_MAX = 90     # від 90 % вологості — майже злива/туман

def should_go_outside(precip_mm: float, humidity: int) -> bool:
    """True («так») — можна виходити; False («ні») — краще лишитись вдома."""
    return precip_mm < PRECIP_MAX_MM and humidity < HUMIDITY_MAX
