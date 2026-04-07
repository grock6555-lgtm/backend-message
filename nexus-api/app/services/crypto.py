import ctypes
import os

_lib = None

def load_crypto_lib():
    global _lib
    if _lib is None:
        lib_path = os.path.join(os.path.dirname(__file__), "../../libnexus_crypto.so")
        if not os.path.exists(lib_path):
            lib_path = "/app/libnexus_crypto.so"
        _lib = ctypes.CDLL(lib_path)
        _lib.verify_prekey_signature.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t)
        _lib.verify_prekey_signature.restype = ctypes.c_int
    return _lib

def verify_prekey(prekey: bytes, signature: bytes, server_public_key: bytes) -> bool:
    lib = load_crypto_lib()
    return lib.verify_prekey_signature(prekey, len(prekey), signature, len(signature), server_public_key, len(server_public_key)) == 1