import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from unittest.mock import MagicMock
from database import SessionLocal

def test_endpoint():
    print("Testing get_clientes_activos_por_plan...")
    
    # Mock request
    mock_request = MagicMock()
    # Mock token inside security
    main.security.get_token_from_request = MagicMock(return_value="valid-token")
    
    db = SessionLocal()
    try:
        res = main.get_clientes_activos_por_plan(request=mock_request, db=db, force_api=False)
        print("Success! Result totals:")
        print(res["totales"])
        print("\nTop 5 planes:")
        for p in res["planes"][:5]:
            print(p)
        print(f"\nTotal clients loaded: {len(res['clientes'])}")
    finally:
        db.close()

if __name__ == "__main__":
    test_endpoint()
