import os



brand = os.getenv("EMAIL_BRAND", "dent-s").lower()

if brand in ("dent-s", "dents", "dent_s"):
    from .dent_s import *
elif brand in ("med.g", "medg", "med_g", "med-g"):
    from .med_g import *
else:
    raise ImportError(f"Unknown EMAIL_BRAND={brand}")
