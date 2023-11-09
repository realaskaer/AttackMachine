import hmac
import ecdsa

from hashlib import sha256, sha512
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Random import get_random_bytes
from ecdsa import SigningKey, keys, SECP256k1
from ecdsa.ellipticcurve import Point


def is_valid_private_key(private_key):
    return 1 <= int.from_bytes(private_key, 'big') < SECP256k1.order


def get_public_key(private_key, encoding='raw'):
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    vk = sk.get_verifying_key()
    return vk.to_string(encoding=encoding)


def derive(private_key_a, public_key_b):
    assert isinstance(private_key_a, bytes), "Неправильный формат закрытого ключа"
    assert len(private_key_a) == 32, "Неправильная длина закрытого ключа"

    assert isinstance(public_key_b, bytes), "Неправильный формат открытого ключа"
    assert len(public_key_b) in [33, 65], "Неправильная длина открытого ключа"

    if len(public_key_b) == 65:
        assert public_key_b[0] == 4, "Неправильный формат открытого ключа"
    if len(public_key_b) == 33:
        assert public_key_b[0] in [2, 3], "Неправильный формат открытого ключа"

    curve = ecdsa.curves.SECP256k1

    key_a = keys.SigningKey.from_string(private_key_a, curve=curve)
    key_b = keys.VerifyingKey.from_string(public_key_b, curve=curve)

    shared_secret = key_a.privkey.secret_multiplier * key_b.pubkey.point

    px = shared_secret.x().to_bytes(32, byteorder='big')
    return px


def hmac_sha256_sign(key, data):
    return hmac.new(key, data, sha256).digest()


def hex_to_uint8_array(hex_string):
    return bytes.fromhex(hex_string)


def uint8_array_to_hex(uint8_array):
    return uint8_array.hex()


def compress(starts_with04):
    test_buffer = bytes.fromhex(starts_with04)
    if len(test_buffer) == 64:
        starts_with04 = '04' + starts_with04

    return uint8_array_to_hex(public_key_convert(hex_to_uint8_array(starts_with04), True))


def decompress(starts_with_02_or_03):

    test_bytes = bytes.fromhex(starts_with_02_or_03)
    if len(test_bytes) == 64:
        starts_with_02_or_03 = '04' + starts_with_02_or_03

    decompressed = uint8_array_to_hex(public_key_convert(hex_to_uint8_array(starts_with_02_or_03), False))

    decompressed = decompressed[2:]
    return decompressed


def public_key_convert(public_key, compressed=False):
    assert len(public_key) == 33 or len(public_key) == 65, "Invalid public key length"

    point = Point.from_bytes(SECP256k1.curve, public_key)

    if compressed:
        result = point.to_bytes(encoding='compressed')
    else:
        result = point.to_bytes(encoding='uncompressed')

    return result


def aes_cbc_encrypt(iv, key, data):
    cipher = AES.new(key, AES.MODE_CBC, iv)

    padding_length = 16 - (len(data) % 16)
    padded_data = data + bytes([padding_length]) * padding_length

    ciphertext = cipher.encrypt(padded_data)
    return ciphertext


def encrypt(public_key_to:bytes, msg: bytes):
    ephem_private_key = get_random_bytes(32)
    while not is_valid_private_key(ephem_private_key):
        ephem_private_key = get_random_bytes(32)

    ephem_public_key = get_public_key(ephem_private_key, 'uncompressed')

    px = derive(ephem_private_key, public_key_to)

    hash_obj = sha512(px)

    iv = get_random_bytes(16)

    encryption_key = hash_obj.digest()[:32]

    mac_key = hash_obj.digest()[32:]

    ciphertext = aes_cbc_encrypt(iv, encryption_key, msg)

    data_to_mac = iv + ephem_public_key + ciphertext
    mac = hmac_sha256_sign(mac_key, data_to_mac)

    ephem_public_key = bytes.fromhex(compress(ephem_public_key.hex()))

    return {
        'iv': iv,
        'ephemPublicKey': ephem_public_key,
        'ciphertext': ciphertext,
        'mac': mac,
    }


def encrypt_with_public_key(public_key, message):

    public_key = decompress(public_key)

    pub_string = '04' + public_key

    encrypted = encrypt(
        bytes.fromhex(pub_string),
        message.encode('utf-8')
    )

    return "".join([
        encrypted['iv'].hex(),
        encrypted['ephemPublicKey'].hex(),
        encrypted['mac'].hex(),
        encrypted['ciphertext'].hex()
    ])


def parse(data_str:str):

    buf = bytes.fromhex(data_str)

    ret = {
        'iv': buf[0:16].hex(),
        'ephemPublicKey': buf[16:49].hex(),
        'mac': buf[49:81].hex(),
        'ciphertext': buf[81:].hex()
    }

    ret['ephemPublicKey'] = '04' + decompress(ret['ephemPublicKey'])

    return ret


def aes_cbc_decrypt(iv, encryption_key, ciphertext):
    cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)


def hmac_sha256_verify(key, msg, sig):
    hmac_obj = hmac.new(key.encode('utf-8'), msg.encode('utf-8'), sha256)

    expected_sig = hmac_obj.digest()

    return hmac.compare_digest(expected_sig, sig)


def decrypt_with_private_key(private_key, encrypted_data):

    encrypted = parse(encrypted_data)

    stripped_key = private_key[2:] if private_key.startswith('0x') else private_key

    encrypted_buffer = {
        'iv': bytes.fromhex(encrypted['iv']),
        'ephemPublicKey': bytes.fromhex(encrypted['ephemPublicKey']),
        'ciphertext': bytes.fromhex(encrypted['ciphertext']),
        'mac': bytes.fromhex(encrypted['mac'])
    }

    derived_key = derive(bytes.fromhex(stripped_key), encrypted_buffer['ephemPublicKey'])
    hash_key = sha512(derived_key).digest()

    encryption_key = hash_key[:32]

    decrypted_message = aes_cbc_decrypt(encrypted_buffer['iv'], encryption_key, encrypted_buffer['ciphertext'])

    return decrypted_message.decode()
