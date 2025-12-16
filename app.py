from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, Response, make_response
import base64
import hashlib
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'change_this_Value'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

BREACH_DATA = {
    'akiner': {
        'hash': '5f4dcc3b5aa765d61d8327deb882cf99',
        'algorithm': 'MD5',
        'source': 'Very Secure Company Breach 2023'
    }
}

WORDLIST = ['password', '123456', 'admin', 'letmein', 'welcome', 'monkey', 'dragon', 'qwerty', '1234567890', 'password123']

DIRECTORY_WORDLIST = ['manager_log_in', 'admin', 'dashboard', 'login', 'api', 'config', 'backup']

MANAGER_USERNAME = 'akiner'
MANAGER_PASSWORD = 'password'  
PORTAL_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Siber Güvenlik Saldırı Simülasyonu</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .objective { background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }
        .link { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        .link:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h1>Siber Güvenlik Saldırı Simülasyonu</h1>
    <div class="objective">
        <h2>Simülasyon Hedefleri</h2>
        <p>Hedefiniz tam saldırı zincirini tamamlamaktır:</p>
        <ol>
            <li>Gizli endpoint'leri keşfet</li>
            <li>Sızdırılmış kimlik bilgilerini bul</li>
            <li>Şifre hash'lerini kır</li>
            <li>İlk erişimi kazan</li>
            <li>Yetkileri yükselt</li>
            <li>Komutları çalıştır</li>
            <li>Final flag'ini elde et - Flag formatı IEEE{...}</li>
        </ol>
        <p><strong>Not:</strong> Tüm etkileşimler tarayıcıda gerçekleşir. Harici araç gerekmez. Dahili sayfaları kullanabilirsiniz.</p>
    </div>
    <h1>Hedef Site</h1>
    <a href="/target" class="link">IEEE Hacettepe</a>
    <h2>Mevcut Araçlar</h2>
    <a href="/dirscan" class="link">Dizin Tarayıcı</a>
    <a href="/breachdb" class="link">Veri İhlali Veritabanı</a>
    <a href="/hashlab" class="link">Hash Kırma Laboratuvarı</a>
    <a href="/files" class="link">Lazım Olabilecek Dosyalar</a>
</body>
</html>
'''

DIRSCAN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dizin Tarayıcı</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
        input, button { padding: 10px; margin: 5px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        .result { margin: 10px 0; padding: 10px; border-left: 4px solid #28a745; background: #f5f5f5; }
        .result-403 { border-left-color: #ffc107; }
        .result-302 { border-left-color: #17a2b8; }
        .result-404 { border-left-color: #dc3545; }
    </style>
</head>
<body>
    <h1>Dizin Tarayıcı</h1>
    <form method="POST">
        <input type="text" name="base_path" value="{{ base_path }}" placeholder="Temel yol" style="width: 300px;" readonly>
        <button type="submit">Tara</button>
    </form>
    <p style="color:#555;">Not: Sadece /target dizini taranabilir.</p>
    {% if results %}
    <h2>Tarama Sonuçları:</h2>
    {% for result in results %}
    <div class="result result-{{ result.status }}">
        <strong>{{ result.path }}</strong> - Durum: {{ result.status }}
        {% if result.status == '302' %}
        <br><em>Yönlendirme tespit edildi</em>
        {% elif result.status == '403' %}
        <br><em>Yasak - kimlik doğrulama gerekli</em>
        {% endif %}
    </div>
    {% endfor %}
    {% endif %}
    <br><a href="/">← Portala Dön</a>
</body>
</html>
'''

BREACHDB_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Veri İhlali Veritabanı</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        input, button { padding: 10px; margin: 5px; }
        button { background: #dc3545; color: white; border: none; cursor: pointer; }
        .result { margin: 20px 0; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; }
        .hash { font-family: monospace; background: #f5f5f5; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Veri İhlali Veritabanı</h1>
    <p>Halka açık veri ihlallerinden sızdırılmış kimlik bilgilerini ara</p>
    <form method="POST">
        <input type="text" name="username" placeholder="Kullanıcı adı veya e-posta" style="width: 300px;">
        <button type="submit">Ara</button>
    </form>
    {% if result %}
    <div class="result">
        <h3>İhlal Bulundu!</h3>
        <p><strong>Kullanıcı Adı:</strong> {{ result.username }}</p>
        <p><strong>Hash:</strong></p>
        <div class="hash">{{ result.hash }}</div>
        <p><strong>Algoritma:</strong> {{ result.algorithm }}</p>
        <p><strong>Kaynak:</strong> {{ result.source }}</p>
        <p><em>Not: Güvenlik nedeniyle şifreler gösterilmez. Hash'i kırmak için HashLab'i kullanın.</em></p>
    </div>
    {% elif searched and not result %}
    <p style="color: #dc3545;">Bu kullanıcı adı için ihlal bulunamadı.</p>
    {% endif %}
    <br><a href="/">← Portala Dön</a>
</body>
</html>
'''

HASHLAB_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hash Kırma</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        input, select, button { padding: 10px; margin: 5px; }
        button { background: #28a745; color: white; border: none; cursor: pointer; }
        .result { margin: 20px 0; padding: 15px; background: #d4edda; border: 1px solid #28a745; }
        .hash { font-family: monospace; background: #f5f5f5; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Hash Kırma</h1>
    <form method="POST">
        <input type="text" name="hash" placeholder="Hash değeri" style="width: 400px;" value="{{ hash_value }}">
        <select name="hash_type">
            <option value="MD5">MD5</option>
        </select>
        <button type="submit">Kır</button>
    </form>
    {% if result %}
    <div class="result">
        <h3>Hash Kırıldı!</h3>
        <p><strong>Düz Metin:</strong> <code>{{ result }}</code></p>
    </div>
    {% elif attempted and not result %}
    <p style="color: #dc3545;">Hash kelime listesinde bulunamadı. Başka bir hash deneyin veya kelime listesini genişletin.</p>
    {% endif %}
    <br><a href="/">← Portala Dön</a>
</body>
</html>
'''

TARGET_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>IEEE Hacettepe</title>
    <style>
        :root {
            --primary: #004aad;
            --secondary: #00b7ff;
            --bg: #f5f7fb;
            --text: #1f2a44;
            --muted: #6b7280;
            --card: #ffffff;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 20px 60px;
            background: var(--bg);
            color: var(--text);
        }
        header {
            background: linear-gradient(120deg, var(--primary), var(--secondary));
            color: white;
            padding: 32px 28px;
            border-radius: 14px;
            margin-top: 40px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.15);
        }
        .pill {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(0,74,173,0.15);
            font-size: 12px;
            letter-spacing: 0.4px;
        }
        .hero-title {
            font-size: 32px;
            margin: 8px 0 4px 0;
        }
        .hero-sub {
            margin: 0;
            font-size: 15px;
            color: #e8f1ff;
        }
        .tagline {
            margin-top: 10px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 18px;
            margin-top: 28px;
        }
        .card {
            background: var(--card);
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.08);
        }
        .card h3 { margin-top: 0; }
        .team-list, .event-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .team-list li, .event-list li {
            padding: 8px 0;
            border-bottom: 1px solid #eef2f7;
        }
        .highlight {
            background: #e9f4ff;
            border-left: 4px solid var(--primary);
            padding: 10px 12px;
            border-radius: 10px;
            font-size: 14px;
        }
        .footer {
            margin-top: 28px;
            font-size: 13px;
            color: var(--muted);
        }
    </style>
</head>
<body>
    <header>
        <div class="pill">Hacettepe Üniversitesi</div>
        <h1 class="hero-title">IEEE Hacettepe</h1>
        <p class="hero-sub">Öğrenci Topluluğu • Teknoloji • Yenilik</p>
        <p class="tagline">Öğrenciler için teknik gelişim, atölyeler ve topluluk deneyimi.</p>
    </header>
    <div class="grid">
        <div class="card">
            <h3>Hakkımızda</h3>
            <p>IEEE Hacettepe, teknoloji ve mühendislik alanlarında öğrencilere destek sağlayan, etkinlikler ve teknik eğitimler düzenleyen bir öğrenci koludur.</p>
            <div class="highlight">Mentorluk, atölye ve yarışmalarla aktif öğrenme imkânı sunuyoruz.</div>
        </div>
        <div class="card">
            <h3>Takımlarımız</h3>
            <ul class="team-list">
                <li>Siber Güvenlik</li>
                <li>Yapay Zeka</li>
                <li>Web Geliştirme</li> <!-- siteyi düzenlememiz gerekebilir -akiner -->
                <li>Oyun Geliştirme</li>
            </ul>
        </div>
        <div class="card">
            <h3>Yaklaşan Etkinlikler</h3>
            <ul class="event-list">
                <li>Pura Game Jam 2026</li>
                <li>Pura Game Jam 2027</li>
                <li>Pura Game Jam 2028</li>
            </ul>
        </div>
    </div>
    <div class="card" style="margin-top:22px;">
        <h3>İletişim</h3>
        <p class="highlight">Sorularınız için: <a href="https://www.instagram.com/ieeehacettepe/">Instagram: @ieeehacettepe</a></p>
    </div>
    <div class="footer">IEEE Hacettepe Öğrenci Kolu • Kampüs içi etkinlik ve teknik topluluk</div>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Yönetici Girişi</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
        input { width: 100%; padding: 10px; margin: 10px 0; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
        .error { color: #dc3545; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Yönetici Portalı</h1>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Kullanıcı adı" required>
        <input type="password" name="password" placeholder="Şifre" required>
        <button type="submit">Giriş Yap</button>
    </form>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Manager Paneli</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
        .dashboard { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .info { background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }
    </style>
</head>
<body>
    <h1>Manager Paneli</h1>
    <div class="dashboard">
        <div class="info">
            <h2>Hoş geldiniz, {{ user }}!</h2>
            <p>Manager olarak giriş yaptınız.</p>
        </div>
        <div class="info">
            <h3>Erişim Seviyeniz</h3>
            <p>Manager sitedeki detayları görüntülemenize olanak sağlar.</p>
        </div>
        <div class="info">
            <h3>Mevcut İşlemler</h3>
            <p>• Ekip raporlarını görüntüle</p>
            <p>• Kaynakları yönet</p>
            <p>• Ekip bilgilerini güncelle</p>
            <!-- cookie değerlerini henüz güvenli hale getiremedim. base64 yeterince güvenli değil, dikkat edin -akiner -->
        </div>
    </div>
    <p><a href="/target">← Ana Sayfaya Dön</a></p>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Yönetici Paneli</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
        .admin-panel { background: #dc3545; color: white; padding: 20px; border-radius: 5px; }
        .upload-section { background: white; color: #333; padding: 20px; margin: 20px 0; border-radius: 5px; }
        input, button { padding: 10px; margin: 5px; }
        button { background: #28a745; color: white; border: none; cursor: pointer; }
        .files { margin: 20px 0; }
        .file-link { display: block; padding: 10px; background: #f5f5f5; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="admin-panel">
        <h1>Yönetici Paneli</h1>
        <p>Hoş geldiniz, Yönetici. Tam sistem erişiminiz var.</p>
    </div>
    <div class="upload-section">
        <h2>Resim Yükleme</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required>
            <button type="submit">Yükle</button>
        </form>
        {% if message %}
        <p style="color: #28a745;">{{ message }}</p>
        {% endif %}
        {% if error %}
        <p style="color: #dc3545;">{{ error }}</p>
        {% endif %}
    </div>
    <div class="upload-section">
        <h2>Yüklenen Dosyalar</h2>
        <div class="files">
            {% for file in files %}
            <a href="/uploads/{{ file }}" class="file-link">{{ file }}</a>
            {% endfor %}
        </div>
    </div>
    <p><a href="/target/dashboard">← Panele Dön</a></p>
</body>
</html>
'''

TERMINAL_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Web Terminal</title>
    <style>
        body { font-family: 'Courier New', monospace; background: #1e1e1e; color: #00ff00; padding: 20px; }
        .terminal { background: #000; padding: 20px; border-radius: 5px; }
        .prompt { color: #00ff00; }
        .root-prompt { color: #ff0000; }
        input { background: #000; color: #00ff00; border: 1px solid #00ff00; padding: 5px; width: 70%; font-family: 'Courier New', monospace; }
        button { background: #00ff00; color: #000; border: none; padding: 5px 15px; cursor: pointer; }
        .output { margin: 10px 0; white-space: pre-wrap; }
        form { margin: 10px 0; }
    </style>
</head>
<body>
    <div class="terminal">
        <h2>Web Terminal</h2>
        <div class="output">
{{ output }}
        </div>
        <form method="POST">
            <span class="{{ prompt_class }}">{{ prompt }}</span>
            <input type="text" name="command" autofocus>
            <button type="submit">Execute</button>
        </form>
        <p style="color: #888; margin-top: 20px;">Supported commands: whoami, id, pwd, ls, sudo -l, cat /root/flag.txt</p>
    </div>
</body>
</html>
'''

FILES_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Lazım Olabilecek Dosyalar</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .file-item { background: #f5f5f5; padding: 20px; margin: 15px 0; border-left: 4px solid #28a745; }
        .download-btn { display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }
        .download-btn:hover { background: #218838; }
        .description { color: #666; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Lazım Olabilecek Dosyalar</h1>
    <p>Bu sayfada simülasyon sırasında kullanılabilecek yardımcı dosyalar bulunmaktadır.</p>
    
    <div class="file-item">
        <h3>Shell Script (shell.php)</h3>
        <p class="description">Web shell scripti. Admin panelinde yüklendiğinde terminal erişimi sağlar.</p>
        <a href="/download/shell.php" class="download-btn">İndir</a>
        <h3>Shell Script (shell.php5)</h3>
        <p class="description">Web shell scripti. Admin panelinde yüklendiğinde terminal erişimi sağlar.</p>
        <a href="/download/shell.php5" class="download-btn">İndir</a>
    </div>
    
    <br><a href="/">← Back to Portal</a>
</body>
</html>
'''

@app.route('/')
def portal():
    return render_template_string(PORTAL_HTML)

@app.route('/dirscan', methods=['GET', 'POST'])
def dirscan():
    base_path = '/target'
    results = []
    
    if request.method == 'POST':
        base_path = '/target'
        for word in DIRECTORY_WORDLIST:
            path = f"{base_path}/{word}"
            if word == 'manager_log_in':
                results.append({'path': path, 'status': '200'})
            elif word == 'admin':
                results.append({'path': path, 'status': '403'})
            elif word == 'dashboard':
                results.append({'path': path, 'status': '302'})
            elif word == 'uploads':
                results.append({'path': path, 'status': '200'})
            else:
                results.append({'path': path, 'status': '404'})
    
    return render_template_string(DIRSCAN_HTML, base_path=base_path, results=results)

@app.route('/breachdb', methods=['GET', 'POST'])
def breachdb():
    result = None
    searched = False
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        searched = True
        if username.lower() in BREACH_DATA:
            result = {
                'username': username,
                **BREACH_DATA[username.lower()]
            }
    
    return render_template_string(BREACHDB_HTML, result=result, searched=searched)

@app.route('/hashlab', methods=['GET', 'POST'])
def hashlab():
    hash_value = ''
    result = None
    attempted = False
    
    if request.method == 'POST':
        hash_value = request.form.get('hash', '').strip()
        hash_type = request.form.get('hash_type', 'MD5')
        attempted = True
        
        if hash_type == 'MD5':
            for word in WORDLIST:
                if hashlib.md5(word.encode()).hexdigest() == hash_value.lower():
                    result = word
                    break
    
    return render_template_string(HASHLAB_HTML, hash_value=hash_value, result=result, attempted=attempted)

@app.route('/target')
def target():
    return render_template_string(TARGET_HTML)

@app.route('/files')
def files():
    return render_template_string(FILES_HTML)

@app.route('/download/shell.php5')
def download_shell_php5():
    shell_content = '''<!--SHELL-->
<!DOCTYPE html>
<html>
<head>
    <title>Shell Script</title>
</head>
<body>
    <h1>Web Shell</h1>
    <p>Bu dosya bir web shell işaretçisi içerir.</p>
    <p>Yönetici paneline yüklendiğinde terminale yönlendirecektir.</p>
    <p>P.S: Bu dosya gerçek bir shell değildir, sadece simülasyon amaçlıdır.</p>
</body>
</html>'''
    return Response(shell_content, mimetype='text/html', headers={'Content-Disposition': 'attachment; filename=shell.php5'})

@app.route('/download/shell.php')
def download_shell_php():
    shell_content = '''<!--SHELL-->
<!DOCTYPE html>
<html>
<head>
    <title>Shell Script</title>
</head>
<body>
    <h1>Web Shell</h1>
    <p>Bu dosya bir web shell işaretçisi içerir.</p>
    <p>Yönetici paneline yüklendiğinde terminale yönlendirecektir.</p>
    <p>P.S: Bu dosya gerçek bir shell değildir, sadece simülasyon amaçlıdır.</p>
</body>
</html>'''
    return Response(shell_content, mimetype='text/html', headers={'Content-Disposition': 'attachment; filename=shell.php'})


@app.route('/target/manager_log_in', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username == MANAGER_USERNAME and password == MANAGER_PASSWORD:
            session['user'] = username
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie('isadmin', base64.b64encode(b'false').decode('utf-8'))
            return resp
        else:
            return render_template_string(LOGIN_HTML, error='Geçersiz kimlik bilgileri')
    
    return render_template_string(LOGIN_HTML)

@app.route('/target/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('manager_login'))
    
    return render_template_string(DASHBOARD_HTML, user=session['user'])

@app.route('/target/admin', methods=['GET', 'POST'])
def admin():
    # Admin durum kontrolü isadmin cookiesi üzerinden yapılıyor.
    isadmin_cookie = request.cookies.get('isadmin', '')
    
    try:
        decoded = base64.b64decode(isadmin_cookie).decode('utf-8')
        if decoded != 'true':
            return redirect(url_for('dashboard'))
    except:
        return redirect(url_for('dashboard'))
    
    files = []
    message = None
    error = None
    
    if request.method == 'POST':
        if 'file' not in request.files:
            error = 'Dosya seçilmedi'
        else:
            file = request.files['file']
            if file.filename == '':
                error = 'Dosya seçilmedi'
            else:
                filename = secure_filename(file.filename)
                
                # Php dışındaki bazı dosya türleri kabul edilir.
                if filename.endswith(('.png', '.png.html', '.png.txt', '.png.php5', '.jpg', '.jpeg', '.php5')):
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    message = f'{filename} dosyası başarıyla yüklendi'
                else:
                    error = 'Geçersiz dosya türü. Sadece resimler kabul edilir.'
    
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    
    return render_template_string(ADMIN_HTML, files=files, message=message, error=error)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):
        # Sadece shell.php5 ve işaretli dosyalar terminal erişimi sağlar.
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if filename.lower() == 'shell.php5' and '<!--SHELL-->' in content:
                    return redirect(url_for('terminal'))
        except:
            pass
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    return 'Dosya bulunamadı', 404

@app.route('/terminal', methods=['GET', 'POST'])
def terminal():
    shell_path = os.path.join(app.config['UPLOAD_FOLDER'], 'shell.php5')
    if not (os.path.exists(shell_path) and '<!--SHELL-->' in open(shell_path, 'r', encoding='utf-8', errors='ignore').read()):
        return redirect(url_for('admin'))
    if 'terminal_state' not in session:
        session['terminal_state'] = {
            'user': 'www-data',
            'is_root': False,
            'history': []
        }
    
    state = session['terminal_state']
    output = ''
    prompt = f"{state['user']}@server:~$ "
    prompt_class = 'prompt'
    
    if state['is_root']:
        prompt = f"root@server:~# "
        prompt_class = 'root-prompt'
    
    if request.method == 'POST':
        command = request.form.get('command', '').strip()
        
        if command == 'whoami':
            output = state['user']
        elif command == 'id':
            if state['is_root']:
                output = 'uid=0(root) gid=0(root) groups=0(root)'
            else:
                output = 'uid=33(www-data) gid=33(www-data) groups=33(www-data)'
        elif command == 'pwd':
            output = '/var/www/html'
        elif command == 'ls':
            output = 'index.html\nconfig.php\nuploads\nlogs'
        elif command == 'sudo -l':
            output = 'Matching Defaults entries for www-data on server:\n    !visiblepw, always_set_home, match_group_by_gid,\n    always_query_group_plugin, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE",\n    env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE",\n    env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES",\n    env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE",\n    env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS _XKB_CHARSET XAUTHORITY",\n    secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n\nUser www-data may run the following commands on server:\n    (ALL) NOPASSWD: /usr/bin/python3 /opt/backup.py'
        elif command.startswith('sudo /usr/bin/python3 /opt/backup.py'):
            state['is_root'] = True
            state['user'] = 'root'
            output = 'Privilege escalation successful. You are now root.'
        elif command == 'cat /root/flag.txt':
            if state['is_root']:
                output = 'IEEE{Sunucu_basariyla_hacklendi}'
            else:
                output = 'cat: /root/flag.txt: Permission denied'
        elif command == 'exit':
            session.pop('terminal_state', None)
            return redirect(url_for('admin'))
        else:
            output = f'bash: {command}: command not found'
        
        state['history'].append({'command': command, 'output': output})
        session['terminal_state'] = state
    
    if state['history']:
        output_lines = []
        for entry in state['history']:
            current_prompt = f"{state['user']}@server:~$ " if not state['is_root'] else "root@server:~# "
            output_lines.append(f"{current_prompt}{entry['command']}")
            output_lines.append(entry['output'])
        output = '\n'.join(output_lines)
    
    return render_template_string(TERMINAL_HTML, output=output, prompt=prompt, prompt_class=prompt_class)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

