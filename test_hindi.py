import requests

url = 'http://127.0.0.1:8000/api/ai/chat/'

questions = ['नमस्ते', 'मुझे सिरदर्द है', 'कल से है', 'गंभीर है', 'बाईं तरफ']

with open('hindi_test_output.txt', 'w', encoding='utf-8') as f:
    for q in questions:
        r = requests.post(url, json={'question': q}, timeout=20)
        ans = r.json()['answer']
        has_hindi = any(ord(c) > 0x900 and ord(c) < 0x980 for c in ans)
        f.write(f'Q: {q}\n')
        f.write(f'A: {ans[:120]}\n')
        f.write(f'Hindi: {has_hindi}\n')
        f.write('\n')