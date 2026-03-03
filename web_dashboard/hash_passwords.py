import streamlit_authenticator as stauth

# Replace these with the actual passwords you want to give your officers
passwords_to_hash =

hashed_passwords = stauth.Hasher(passwords_to_hash).generate()
print(hashed_passwords)