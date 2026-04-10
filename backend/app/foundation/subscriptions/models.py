from typing import Literal

SubscriptionState = Literal["trial_active", "active", "past_due", "read_only", "cancelled"]
BillingCadence = Literal["monthly", "annual"]
