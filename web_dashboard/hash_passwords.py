import streamlit_authenticator as stauth

# Replace these with the actual passwords you want to give your officers
passwords_to_hash = ['officer1_password', 'officer2_password', 'admin_password']

hashed_passwords = stauth.Hasher(passwords_to_hash).generate()
print(hashed_passwords)