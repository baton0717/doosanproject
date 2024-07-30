from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_uploads import UploadSet, configure_uploads, ALL, DOCUMENTS
import pytesseract
import fitz  # PyMuPDF
import os
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for matplotlib
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOADED_FILES_DEST'] = 'uploads'

# Tesseract 경로 설정 (Windows의 경우 필요)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 허용된 파일 확장자 설정
files = UploadSet('files', ('pdf', 'doc', 'docx', 'txt', 'rtf'))
configure_uploads(app, files)

# Custom email validator for doosan.com domain
def doosan_email(form, field):
    if not field.data.endswith('@doosan.com'):
        raise ValidationError('두산 계정만 사용할 수 있습니다.')

class RegistrationForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email(), doosan_email])
    password = PasswordField('비밀번호', validators=[DataRequired(), EqualTo('confirm', message='비밀번호가 일치하지 않습니다.')])
    confirm = PasswordField('비밀번호 확인')
    send_code = SubmitField('인증번호 발송')
    submit = SubmitField('가입')

class LoginForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('로그인')

class FileUploadForm(FlaskForm):
    file = FileField('파일', validators=[DataRequired()])
    submit = SubmitField('업로드')

@app.route('/')
def index():
    # 샘플 그래프 생성
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [10, 20, 25, 30])
    ax.set(xlabel='날짜', ylabel='사용량',
           title='Doosan AI Co-innovation 일간 사용량')
    ax.grid()

    # 그래프를 이미지로 변환
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close(fig)
    return render_template('index.html', graph_url='data:image/png;base64,{}'.format(graph_url))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.send_code.data:
            # 인증번호 발송 로직을 여기에 추가하세요
            flash('인증번호가 발송되었습니다!', 'success')
        else:
            # 회원가입 로직을 여기에 추가하세요
            flash('성공적으로 가입되었습니다!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # 로그인 로직을 여기에 추가하세요
        flash('성공적으로 로그인되었습니다!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    # 로그아웃 로직을 여기에 추가하세요
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('index'))

@app.route('/notices')
def notices():
    return render_template('notices.html')

@app.route('/task/<int:task_id>')
def task(task_id):
    return render_template('task.html', task_id=task_id)

@app.route('/task2', methods=['GET', 'POST'])
def task2():
    form = FileUploadForm()
    ocr_text = None
    if form.validate_on_submit():
        filename = files.save(request.files['file'])
        file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], filename)
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text("text")
            ocr_text = text

            # OCR 처리된 텍스트를 파일로 저장
            output_txt_path = os.path.join(app.config['UPLOADED_FILES_DEST'], f"{os.path.splitext(filename)[0]}.txt")
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write(text)

            return render_template('task2.html', form=form, ocr_text=ocr_text, download_link=url_for('download_file', filename=f"{os.path.splitext(filename)[0]}.txt"))
        except Exception as e:
            flash(f'OCR 처리 중 오류가 발생했습니다: {str(e)}')
    return render_template('task2.html', form=form)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
