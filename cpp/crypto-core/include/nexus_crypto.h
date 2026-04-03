#ifndef NEXUS_CRYPTO_H
#define NEXUS_CRYPTO_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ========== Identity keypair (Ed25519) ==========
void* identity_keypair_generate(void);
void identity_keypair_free(void* kp);
void identity_keypair_get_public(const void* kp, uint8_t* out_pub, size_t* out_len);
void identity_keypair_get_private(const void* kp, uint8_t* out_priv, size_t* out_len);

// ========== Prekey bundle (Signal) ==========
void* prekey_bundle_create(void* identity_keypair, uint32_t prekey_id, uint32_t signed_prekey_id);
void prekey_bundle_free(void* bundle);
void prekey_bundle_serialize(const void* bundle, uint8_t** out_data, size_t* out_len);
void prekey_bundle_deserialize(const uint8_t* data, size_t len, void** out_bundle);

// ========== E2EE session ==========
void* session_create_from_prekey(const uint8_t* remote_prekey_bundle, size_t bundle_len);
void session_destroy(void* session);
int session_encrypt(void* session, const uint8_t* plaintext, size_t pt_len,
                    uint8_t** ciphertext, size_t* ct_len);
int session_decrypt(void* session, const uint8_t* ciphertext, size_t ct_len,
                    uint8_t** plaintext, size_t* pt_len);

// ========== Post-quantum hybrid (Kyber-768) ==========
void* pq_session_create(const uint8_t* remote_public_key, size_t key_len);
void pq_session_destroy(void* session);
int hybrid_encrypt(void* pq_session, const uint8_t* plaintext, size_t pt_len,
                   uint8_t** ciphertext, size_t* ct_len);
int hybrid_decrypt(void* pq_session, const uint8_t* ciphertext, size_t ct_len,
                   uint8_t** plaintext, size_t* pt_len);

// ========== Server-side prekey verification ==========
int verify_prekey_signature(const uint8_t* prekey_data, size_t prekey_len,
                            const uint8_t* signature, size_t sig_len,
                            const uint8_t* server_public_key, size_t key_len);

// ========== Optional: Key Escrow (only if NEXUS_ENABLE_ESCROW is defined) ==========
// These functions allow the server to store an encrypted copy of the session key
// during session creation, so that a trusted developer (with master key) can later
// decrypt messages for debugging or legal purposes.
// By default, this feature is DISABLED.
#ifdef NEXUS_ENABLE_ESCROW
// Call this immediately after session_create_from_prekey, before any encryption.
// It will encrypt the session's root key with the provided master public key (RSA-2048 or similar)
// and return an escrow blob that the server can store.
void* session_export_escrow_blob(void* session, const uint8_t* master_public_key, size_t key_len, size_t* out_blob_len);

// Server-side: decrypt a message using the escrow blob and the master private key.
// This reconstructs the session key and decrypts the message.
int session_decrypt_with_escrow(const uint8_t* ciphertext, size_t ct_len,
                                uint8_t** plaintext, size_t* pt_len,
                                const uint8_t* escrow_blob, size_t blob_len,
                                const uint8_t* master_private_key, size_t key_len);
#endif

#ifdef __cplusplus
}
#endif

#endif