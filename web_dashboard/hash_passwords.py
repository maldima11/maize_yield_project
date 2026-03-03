import streamlit_authenticator as stauth

hashed1 = stauth.Hasher.hash('secureAdmin99')
hashed2 = stauth.Hasher.hash('secureAdmin98')

print("Hashed Password 1:", hashed1)
print("Hashed Password 2:", hashed2)