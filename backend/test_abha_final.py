import requests
import re

s = requests.Session()
r = requests.get('http://127.0.0.1:8000/patient/login/', timeout=10)
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text).group(1)

r2 = requests.post(
    'http://127.0.0.1:8000/patient/login/',
    data={'patient_id': 'PAT0001', 'password': 'secret123', 'csrfmiddlewaretoken': r.cookies.get('csrftoken')},
    cookies=r.cookies,
    timeout=10,
    allow_redirects=False
)
print('Login status:', r2.status_code)
print('Redirect to:', r2.headers.get('Location'))

r3 = requests.get('http://127.0.0.1:8000/patient/profile/', cookies=r2.cookies, timeout=10)
print('Profile status:', r3.status_code)
print('Length:', len(r3.text))
print('Has ABHA:', 'ABHA Health ID' in r3.text)
print('Has Number:', '4834-5835-5786-04' in r3.text)
print('Has Addr:', 'kunal@abdm' in r3.text)
print('Has patient.abha_profile:', 'patient.abha_profile' in r3.text)
if 'ABHA Health ID' not in r3.text:
    idx = r3.text.find('patient.abha_profile')
    if idx >= 0:
        print('Found patient.abha_profile at:', idx)
    else:
        print('patient.abha_profile NOT in response')
        idx = r3.text.find('Record Type')
        if idx >= 0:
            print('Record Type found at:', r3.text.find('Record Type'))
            print(r3.text[max(0,r3.text.find('Record Type')-300):r3.text.find('Record Type')+300])