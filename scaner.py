import requests

TARGET_URL = 'http://127.0.0.1:5000'

def scan_xss():
    payload = "<script>alert(1)</script>"
    response = requests.get(f'{TARGET_URL}/', params={'q':payload})

    if payload in response.text:
        print('[!] Уязвимость XSS обнаружена!')
        print(f'Пейлоад: {payload}')
        print(f'Параметр: q')
    else:
        print("[-] XSS не обнаружен. Сервер безопасно экранирует вывод.")
      
def scan_sqli():
    payload = "' OR 1=1 --"
    data = {
        "username": payload,
        "password": 'x'
    }
    response = requests.post(f'{TARGET_URL}/login',data=data,allow_redirects=False)
    if response.status_code == 302 and '/admin' in response.headers.get('Location',''):
        print('[!] Уязвимость SQL-Injection обнаружена!')
        print(f'Пейлоад: {payload}')
        print(f'Параметр: username')
    else:
        print("[-] SQL-Injection не обнаружена. Сервер использует безопасные запросы.")
      
if __name__=='__main__':
    scan_xss()
    scan_sqli()
