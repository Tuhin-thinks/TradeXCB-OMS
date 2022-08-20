"""
Script to deal with data encryption/descriptions and data security
"""

import getmac
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA256
from Cryptodome.Util.Padding import pad, unpad


def generate_hash(sec_question: str, sec_answer: str) -> str:
    """
    Function to generate hash for security question and security answer
    :param sec_question: user entered security question
    :param sec_answer: user entered security answer
    :return: hashed string
    """
    hash_obj = SHA256.new()
    hash_obj.update(sec_question[::-1].encode("UTF-16"))
    hash_obj.update(sec_answer[::-1].encode("UTF-16"))
    return hash_obj.hexdigest()


def generate_password_hash(plain_txt_passwd: str, email_id: str) -> str:
    hash_obj = SHA256.new()
    hash_obj.update(plain_txt_passwd.encode("UTF-16"))
    hash_obj.update(email_id.encode("UTF-16"))
    return hash_obj.hexdigest()


def encrypt(plain_string: str, m_id: str) -> str:
    if m_id is None:
        m_id = "nomail@mail.org"
    key = pad(m_id.encode('utf-8'), 16)
    nonce = pad(getmac.get_mac_address().encode('utf-8'), 16)  # user's mac address
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    ciphertext = cipher.encrypt(pad(plain_string.encode('utf-8'), 16)).hex()
    return ciphertext


def decrypt(cipher_text: str, m_id: str) -> str:
    """
    returns password decrypted, else returns empty-string
    """
    try:
        if m_id is None:
            m_id = "nomail@mail.org"
        key = pad(m_id.encode('utf-8'), 16)
        nonce = pad(getmac.get_mac_address().encode('utf-8'), 16)  # nonce will be based on user's mac address
        aes_obj = AES.new(key, AES.MODE_EAX, nonce)
        data = unpad(aes_obj.decrypt(bytes.fromhex(cipher_text)), 16)
        pwd_string = data.decode('UTF-8')
        return pwd_string
    except Exception as e:
        return ""


def r_shift(s: str):
    place = 2
    a = s[:-place]
    b = s[-place:]
    return b + a


def reset_shift(shifted_s: str):
    place = 2
    a = shifted_s[:place]
    b = shifted_s[place:]
    return b + a


def encrypt_db_pass(dec_pass: str, m_id: str):
    if m_id is None:
        m_id = "nomail@mail.org"
    shifted_mid = pad(r_shift(m_id[::-1]).encode('UTF-8'), 16)
    nonce = pad(r_shift(m_id).encode('UTF-8'), 16)
    aes = AES.new(key=shifted_mid, mode=AES.MODE_EAX, nonce=nonce)
    enc_pass = aes.encrypt(pad(dec_pass.encode('UTF-8'), 16)).hex()
    return enc_pass


def decrypt_db_pass(enc_pass: str, m_id: str):
    try:
        if m_id is None:
            m_id = "nomail@mail.org"
        shifted_mid = pad(r_shift(m_id[::-1]).encode('UTF-8'), 16)
        nonce = pad(r_shift(m_id).encode('UTF-8'), 16)
        aes = AES.new(key=shifted_mid, mode=AES.MODE_EAX, nonce=nonce)
        psswd_dec = unpad(aes.decrypt(bytes.fromhex(enc_pass)), 16).decode('UTF-8')
        return psswd_dec
    except Exception as e:
        return ""


if __name__ == '__main__':
    pass
