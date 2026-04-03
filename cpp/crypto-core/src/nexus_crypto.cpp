#include "nexus_crypto.h"
#include <sodium.h>
#include <signal_protocol.h>
#include <oqs/oqs.h>
#include <cstring>
#include <cstdlib>
#include <stdexcept>
#include <vector>
#include <memory>

// ========== Глобальный контекст Signal ==========
static signal_context* g_ctx = nullptr;
static void ensure_ctx() {
    if (!g_ctx) {
        signal_context_create(&g_ctx, nullptr, nullptr, nullptr);
        signal_context_set_crypto_provider(g_ctx, &sodium_crypto_provider);
    }
}

// ========== Вспомогательные структуры ==========
struct identity_keypair { uint8_t pub[32]; uint8_t priv[64]; };
struct prekey_bundle { session_prekey_bundle* bundle; };
struct session_cipher_ctx {
    session_cipher* cipher;
    session_record* record;
    signal_context* ctx;
};
struct pq_session {
    uint8_t remote_pub[OQS_KEM_kyber_768_public_key_length];
    uint8_t local_priv[OQS_KEM_kyber_768_secret_key_length];
    uint8_t local_pub[OQS_KEM_kyber_768_public_key_length];
    bool ready;
};

// ========== Identity ==========
void* identity_keypair_generate() {
    if (sodium_init() < 0) return nullptr;
    auto* kp = new identity_keypair();
    crypto_sign_keypair(kp->pub, kp->priv);
    return kp;
}
void identity_keypair_free(void* kp) { delete static_cast<identity_keypair*>(kp); }
void identity_keypair_get_public(const void* kp, uint8_t* out, size_t* len) { *len = 32; memcpy(out, ((identity_keypair*)kp)->pub, 32); }
void identity_keypair_get_private(const void* kp, uint8_t* out, size_t* len) { *len = 64; memcpy(out, ((identity_keypair*)kp)->priv, 64); }

// ========== Prekey bundle ==========
void* prekey_bundle_create(void* ikp, uint32_t prekey_id, uint32_t signed_prekey_id) {
    ensure_ctx();
    auto* kp = (identity_keypair*)ikp;
    auto* bundle = new prekey_bundle();

    // Prekey (ECDH)
    uint8_t pre_priv[32], pre_pub[32];
    crypto_scalarmult_curve25519_base(pre_pub, pre_priv);
    session_pre_key* prekey = nullptr;
    session_pre_key_create(&prekey, prekey_id, pre_pub, pre_priv, g_ctx);

    // Signed prekey (Ed25519)
    uint8_t sig_priv[64], sig_pub[32];
    crypto_sign_keypair(sig_pub, sig_priv);
    session_signed_pre_key* signed_prekey = nullptr;
    session_signed_pre_key_create(&signed_prekey, signed_prekey_id, sig_pub, sig_priv, 0, g_ctx);

    // Identity
    session_identity_key* identity = nullptr;
    session_identity_key_create(&identity, kp->pub, kp->priv, g_ctx);

    session_prekey_bundle_create(&bundle->bundle, identity, prekey, signed_prekey, nullptr, 0, g_ctx);

    session_pre_key_destroy(prekey);
    session_signed_pre_key_destroy(signed_prekey);
    session_identity_key_destroy(identity);
    return bundle;
}
void prekey_bundle_free(void* b) { auto* p = (prekey_bundle*)b; if(p->bundle) session_prekey_bundle_destroy(p->bundle); delete p; }
void prekey_bundle_serialize(const void* b, uint8_t** out, size_t* len) {
    auto* p = (prekey_bundle*)b;
    signal_buffer* buf = session_prekey_bundle_serialize(p->bundle);
    *len = signal_buffer_len(buf);
    *out = (uint8_t*)malloc(*len);
    memcpy(*out, signal_buffer_data(buf), *len);
    signal_buffer_free(buf);
}
void prekey_bundle_deserialize(const uint8_t* data, size_t len, void** out) {
    ensure_ctx();
    auto* p = new prekey_bundle();
    if (session_prekey_bundle_deserialize(&p->bundle, data, len, g_ctx) != 0) { delete p; throw std::runtime_error("deserialize"); }
    *out = p;
}

// ========== Session ==========
void* session_create_from_prekey(const uint8_t* data, size_t len) {
    ensure_ctx();
    auto* ctx = new session_cipher_ctx();
    ctx->ctx = g_ctx;

    session_prekey_bundle* remote = nullptr;
    if (session_prekey_bundle_deserialize(&remote, data, len, g_ctx) != 0) { delete ctx; return nullptr; }
    session_builder* builder = nullptr;
    session_builder_create(&builder, g_ctx, 0, 0);
    if (session_builder_process_prekey_bundle(builder, remote) != 0) { session_builder_destroy(builder); session_prekey_bundle_destroy(remote); delete ctx; return nullptr; }
    session_builder_get_session_record(builder, &ctx->record);
    session_cipher_create(&ctx->cipher, g_ctx, 0, ctx->record);
    session_builder_destroy(builder);
    session_prekey_bundle_destroy(remote);
    return ctx;
}
void session_destroy(void* s) {
    auto* ctx = (session_cipher_ctx*)s;
    if(ctx->cipher) session_cipher_destroy(ctx->cipher);
    if(ctx->record) session_record_destroy(ctx->record);
    delete ctx;
}
int session_encrypt(void* s, const uint8_t* pt, size_t pt_len, uint8_t** ct, size_t* ct_len) {
    auto* ctx = (session_cipher_ctx*)s;
    signal_buffer* buf = session_cipher_encrypt(ctx->cipher, pt, pt_len, nullptr);
    if(!buf) return -1;
    *ct_len = signal_buffer_len(buf);
    *ct = (uint8_t*)malloc(*ct_len);
    memcpy(*ct, signal_buffer_data(buf), *ct_len);
    signal_buffer_free(buf);
    return 0;
}
int session_decrypt(void* s, const uint8_t* ct, size_t ct_len, uint8_t** pt, size_t* pt_len) {
    auto* ctx = (session_cipher_ctx*)s;
    signal_buffer* buf = session_cipher_decrypt(ctx->cipher, ct, ct_len, nullptr);
    if(!buf) return -1;
    *pt_len = signal_buffer_len(buf);
    *pt = (uint8_t*)malloc(*pt_len);
    memcpy(*pt, signal_buffer_data(buf), *pt_len);
    signal_buffer_free(buf);
    return 0;
}

// ========== Post-quantum hybrid ==========
void* pq_session_create(const uint8_t* remote_pub, size_t key_len) {
    if(key_len != OQS_KEM_kyber_768_public_key_length) return nullptr;
    auto* s = new pq_session();
    memcpy(s->remote_pub, remote_pub, key_len);
    OQS_KEM* kem = OQS_KEM_new(OQS_KEM_alg_kyber_768);
    OQS_KEM_keypair(kem, s->local_pub, s->local_priv);
    OQS_KEM_free(kem);
    s->ready = true;
    return s;
}
void pq_session_destroy(void* s) { delete (pq_session*)s; }
int hybrid_encrypt(void* s, const uint8_t* pt, size_t pt_len, uint8_t** ct, size_t* ct_len) {
    auto* sess = (pq_session*)s;
    if(!sess->ready) return -1;
    uint8_t ss[OQS_KEM_kyber_768_shared_secret_length];
    uint8_t kem_ct[OQS_KEM_kyber_768_ciphertext_length];
    OQS_KEM* kem = OQS_KEM_new(OQS_KEM_alg_kyber_768);
    OQS_KEM_encaps(kem, kem_ct, ss, sess->remote_pub);
    OQS_KEM_free(kem);
    uint8_t nonce[12];
    randombytes_buf(nonce, 12);
    std::vector<uint8_t> cipher(pt_len + 16);
    unsigned long long clen;
    crypto_aead_aes256gcm_encrypt(cipher.data(), &clen, pt, pt_len, nullptr, 0, nonce, ss);
    *ct_len = 12 + OQS_KEM_kyber_768_ciphertext_length + clen;
    *ct = (uint8_t*)malloc(*ct_len);
    memcpy(*ct, nonce, 12);
    memcpy(*ct+12, kem_ct, OQS_KEM_kyber_768_ciphertext_length);
    memcpy(*ct+12+OQS_KEM_kyber_768_ciphertext_length, cipher.data(), clen);
    return 0;
}
int hybrid_decrypt(void* s, const uint8_t* ct, size_t ct_len, uint8_t** pt, size_t* pt_len) {
    auto* sess = (pq_session*)s;
    if(!sess->ready || ct_len < 12+OQS_KEM_kyber_768_ciphertext_length) return -1;
    const uint8_t* nonce = ct;
    const uint8_t* kem_ct = ct+12;
    const uint8_t* enc = ct+12+OQS_KEM_kyber_768_ciphertext_length;
    size_t enc_len = ct_len - 12 - OQS_KEM_kyber_768_ciphertext_length;
    uint8_t ss[OQS_KEM_kyber_768_shared_secret_length];
    OQS_KEM* kem = OQS_KEM_new(OQS_KEM_alg_kyber_768);
    OQS_KEM_decaps(kem, ss, kem_ct, sess->local_priv);
    OQS_KEM_free(kem);
    std::vector<uint8_t> plain(enc_len);
    unsigned long long plen;
    if(crypto_aead_aes256gcm_decrypt(plain.data(), &plen, nullptr, enc, enc_len, nullptr, 0, nonce, ss) != 0) return -1;
    *pt_len = plen;
    *pt = (uint8_t*)malloc(plen);
    memcpy(*pt, plain.data(), plen);
    return 0;
}

// ========== Server signature verification ==========
int verify_prekey_signature(const uint8_t* prekey, size_t prekey_len,
                            const uint8_t* sig, size_t sig_len,
                            const uint8_t* pubkey, size_t key_len) {
    if(sodium_init()<0) return 0;
    if(key_len != 32 || sig_len != 64) return 0;
    return crypto_sign_verify_detached(sig, prekey, prekey_len, pubkey) == 0;
}