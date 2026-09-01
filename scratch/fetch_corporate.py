import urllib.request
import urllib.parse
import json
import time
from collections import defaultdict

def analyze_corporate_data():
    login_url = "https://powerlink.rubpi.com/api/login"
    creds = {"username": "api_exp", "password": "-?J+\\FcmKT2zWl5A28=~"}
    data = json.dumps(creds).encode('utf-8')

    req = urllib.request.Request(login_url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode())
        api_token = res_data.get('token') or res_data.get('access_token')

    export_url = "https://powerlink.rubpi.com/api/exports/users?is_natural=false"
    req2 = urllib.request.Request(export_url, headers={'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}, method='POST')
    with urllib.request.urlopen(req2) as response:
        res2_data = json.loads(response.read().decode())
        task_id = res2_data.get('task_id')

    get_url = f"https://powerlink.rubpi.com/api/exports/users/{task_id}"
    for i in range(20):
        time.sleep(2)
        req3 = urllib.request.Request(get_url, headers={'Authorization': f'Bearer {api_token}'}, method='GET')
        try:
            with urllib.request.urlopen(req3) as resp3:
                data_corp = json.loads(resp3.read().decode())
                break
        except urllib.error.HTTPError as e:
            if e.code == 400:
                continue
            raise

    # Save to static/uploads/last_snapshot_corporativo.json
    with open('static/uploads/last_snapshot_corporativo.json', 'w', encoding='utf-8') as f:
        json.dump(data_corp, f)

    users = data_corp.get('data', [])
    print(f"Total corporate users: {len(users)}")

    plan_stats = defaultdict(lambda: {'count': 0, 'total_amount': 0.0})
    total_activos = 0
    total_costo = 0.0

    for u in users:
        st = str(u.get('service_status', '')).strip().upper()
        if st in ('ACTIVO', 'ACT.'):
            plan = str(u.get('plan', '')).strip() or 'Sin Plan'
            try:
                amt = float(u.get('amount') or 0.0)
            except:
                amt = 0.0
            plan_stats[plan]['count'] += 1
            plan_stats[plan]['total_amount'] += amt
            total_activos += 1
            total_costo += amt

    print(f"Corporate Activos: {total_activos} | Facturación Total: ${total_costo:,.2f}")
    for p, s in sorted(plan_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"  {p:45} | Clientes: {s['count']:4} | Total: ${s['total_amount']:10,.2f}")

if __name__ == "__main__":
    analyze_corporate_data()
