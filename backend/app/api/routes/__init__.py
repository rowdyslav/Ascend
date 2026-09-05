from . import analytics, body_metrics, days, lab, nutrition, protocol, workouts

ROUTERS = [
    days.router, body_metrics.router, workouts.router, nutrition.router,
    protocol.router, lab.router, analytics.router,
]
