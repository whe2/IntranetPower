import json
import os
from collections import defaultdict

UPLOAD_DIR = "static/uploads"

def build_plan_summary(users):
    total_activos = 0
    total_monto = 0.0
    datos_clientes_activos = []
    plan_aggregates = {}

    for item in users:
        status = str(item.get('service_status', '')).strip().upper()
        if status in ('ACTIVO', 'ACT.'):
            plan = str(item.get('plan', '')).strip() or 'Sin Plan'
            service_type = str(item.get('service_type', '')).strip().upper()
            
            if plan.upper() == 'IPTV' or service_type == 'IPTV':
                continue
                
            try:
                amount = float(item.get('amount') or 0.0)
            except:
                amount = 0.0
                
            try:
                balance = float(item.get('balance') or 0.0)
            except:
                balance = 0.0

            raw_inst = item.get('creation_date', '')
            fecha_inst = str(raw_inst)
            if raw_inst and 'T' in str(raw_inst):
                fecha_inst = str(raw_inst).split('T')[0]

            sid = str(item.get('id_servicio', '')).strip()
            cedula = f"{item.get('doc_type', '')}-{item.get('doc', '')}" if item.get('doc') else ""
            nombre = str(item.get('name', '')).strip()
            urbanismo = str(item.get('urban', '')).strip()
            telefono = str(item.get('phone', '')).strip()

            total_activos += 1
            total_monto += amount

            datos_clientes_activos.append({
                'ID Servicio': sid,
                'Cédula': cedula,
                'Nombres': nombre,
                'Plan': plan,
                'Tipo de servicio': service_type,
                'Costo del plan': amount,
                'Estado servicio': 'Act.',
                'Saldo Actual': balance,
                'Fecha de instalación': fecha_inst,
                'Teléfono 1': telefono,
                'Urbanismo': urbanismo
            })

            if plan not in plan_aggregates:
                plan_aggregates[plan] = {
                    'Plan': plan,
                    'Cantidad': 0,
                    'Sumatoria Costo': 0.0,
                    'Precios': set()
                }
            plan_aggregates[plan]['Cantidad'] += 1
            plan_aggregates[plan]['Sumatoria Costo'] += amount
            plan_aggregates[plan]['Precios'].add(amount)

    datos_planes_activos = []
    for p_name, p_data in plan_aggregates.items():
        cnt = p_data['Cantidad']
        tot_cost = p_data['Sumatoria Costo']
        precios_list = sorted(list(p_data['Precios']))
        precio_unitario_str = " / ".join([f"${p:g}" for p in precios_list]) if precios_list else "$0.00"
        precio_ref = precios_list[0] if len(precios_list) == 1 else (tot_cost / cnt if cnt > 0 else 0.0)

        datos_planes_activos.append({
            'Plan': p_name,
            'Cantidad': cnt,
            'Precio Unitario': precio_unitario_str,
            'Precio Referencia': round(precio_ref, 2),
            'Sumatoria Costo': round(tot_cost, 2),
            'Porcentaje Clientes': round((cnt / total_activos * 100), 2) if total_activos > 0 else 0.0,
            'Porcentaje Ingresos': round((tot_cost / total_monto * 100), 2) if total_monto > 0 else 0.0
        })

    datos_planes_activos.sort(key=lambda x: x['Cantidad'], reverse=True)
    plan_lider = datos_planes_activos[0]['Plan'] if datos_planes_activos else ''

    return {
        "totales": {
            "total_clientes_activos": total_activos,
            "total_costo_facturacion": round(total_monto, 2),
            "total_planes": len(datos_planes_activos),
            "plan_lider": plan_lider
        },
        "planes": datos_planes_activos,
        "clientes": datos_clientes_activos
    }

def test_simultaneous():
    with open('static/uploads/last_snapshot.json', 'r', encoding='utf-8') as f:
        gen_data = json.load(f).get('data', [])
        
    with open('static/uploads/last_snapshot_corporativo.json', 'r', encoding='utf-8') as f:
        corp_data = json.load(f).get('data', [])

    # Corporate service IDs
    corp_sids = {str(u.get('id_servicio', '')).strip() for u in corp_data if str(u.get('id_servicio', '')).strip()}
    
    # Residencial: General minus Corporate IDs (or is_natural == True)
    res_data = [u for u in gen_data if str(u.get('id_servicio', '')).strip() not in corp_sids]

    # Consolidado: Union by service ID
    all_dict = {}
    for u in res_data:
        sid = str(u.get('id_servicio', '')).strip()
        if sid: all_dict[sid] = u
    for u in corp_data:
        sid = str(u.get('id_servicio', '')).strip()
        if sid: all_dict[sid] = u
    cons_data = list(all_dict.values())

    res_resumen = build_plan_summary(res_data)
    corp_resumen = build_plan_summary(corp_data)
    cons_resumen = build_plan_summary(cons_data)

    print("=== 1. CUADRO RESIDENCIAL ===")
    print(f"Clientes Activos: {res_resumen['totales']['total_clientes_activos']} | Facturación: ${res_resumen['totales']['total_costo_facturacion']:,.2f} | Planes: {res_resumen['totales']['total_planes']}")
    
    print("\n=== 2. CUADRO CORPORATIVO ===")
    print(f"Clientes Activos: {corp_resumen['totales']['total_clientes_activos']} | Facturación: ${corp_resumen['totales']['total_costo_facturacion']:,.2f} | Planes: {corp_resumen['totales']['total_planes']}")

    print("\n=== 3. CUADRO CONSOLIDADO (UNIÓN DE AMBOS) ===")
    print(f"Clientes Activos: {cons_resumen['totales']['total_clientes_activos']} | Facturación: ${cons_resumen['totales']['total_costo_facturacion']:,.2f} | Planes: {cons_resumen['totales']['total_planes']}")

if __name__ == '__main__':
    test_simultaneous()
