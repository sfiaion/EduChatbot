import os
import sys
import pathlib
BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
from app.services.faiss_service import FaissService
def main():
    svc = FaissService(dim=768)
    print("index_path:", os.path.abspath(svc.index_path))
    print("vectors_path:", os.path.abspath(svc.vectors_path))
    print("ntotal:", svc.index.ntotal)
    ids = list(svc.id2vector.keys())
    print("ids_count:", len(ids))
    print("ids_sample:", ids[:20])
    if ids:
        first = ids[0]
        v = svc.get_vector_by_id(first)
        print("first_id:", first)
        print("vector_shape:", getattr(v, "shape", None))
if __name__ == "__main__":
    main()
