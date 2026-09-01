import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from unittest.mock import MagicMock
from database import SessionLocal
import main

async def test_procesar():
    print("Testing procesar_auditoria_api...")
    mock_request = MagicMock()
    main.security.get_token_from_request = MagicMock(return_value="valid-token")
    
    db = SessionLocal()
    try:
        res = await main.procesar_auditoria_api(
            request=mock_request,
            db=db,
            fileOld=None,
            fechaCorte="2026-07-01",
            fechaInstalaciones="2026-07-13"
        )
        print("Success! Keys in response:", list(res.keys()))
        print(f"Planes activos count: {len(res.get('planesActivos', []))}")
        print(f"Clientes activos count: {len(res.get('clientesActivos', []))}")
        if res.get('planesActivos'):
            print("First plan in list:", res['planesActivos'][0])
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_procesar())
