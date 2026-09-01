import json
from collections import defaultdict

with open('static/uploads/last_snapshot.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

users = data.get('data', [])

plan_stats = defaultdict(lambda: {'count': 0, 'total_amount': 0.0, 'plans_individual_amounts': defaultdict(int)})
total_activos = 0
total_monto = 0.0

for u in users:
    status = str(u.get('service_status', '')).strip().upper()
    if status in ('ACTIVO', 'ACT.'):
        plan = str(u.get('plan', '')).strip() or 'Sin Plan'
        service_type = str(u.get('service_type', '')).strip()
        try:
            amount = float(u.get('amount') or 0)
        except:
            amount = 0.0
        
        plan_stats[plan]['count'] += 1
        plan_stats[plan]['total_amount'] += amount
        plan_stats[plan]['plans_individual_amounts'][amount] += 1
        total_activos += 1
        total_monto += amount

print(f'Total Activos: {total_activos} | Monto Total: ${total_monto:,.2f}')
sorted_plans = sorted(plan_stats.items(), key=lambda x: x[1]['count'], reverse=True)
for plan, stats in sorted_plans:
    amounts_str = ", ".join([f"${amt} (x{cnt})" for amt, cnt in sorted(stats['plans_individual_amounts'].items())])
    print(f"{plan:45} | Cantidad: {stats['count']:5} | Sumatoria: ${stats['total_amount']:10,.2f} | Precios: {amounts_str}")
