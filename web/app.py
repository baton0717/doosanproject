from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_uploads import UploadSet, configure_uploads, ALL, DOCUMENTS
import pytesseract
import fitz  # PyMuPDF
import os
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import io
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOADED_FILES_DEST'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Tesseract 경로 설정 (Windows의 경우 필요)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 허용된 파일 확장자 설정
files = UploadSet('files', ('pdf', 'doc', 'docx', 'txt', 'rtf'))
configure_uploads(app, files)

# 한글 폰트 설정
font_path = 'C:/Windows/Fonts/malgun.ttf'  # Windows에서 사용하는 폰트 경로 예시
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)

# 사용자 모델 정의
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# 게시물 모델 정의
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(200), nullable=True)

# 회사명와 매칭되는 회사코드 정의
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(10), nullable=False)

# 데이터베이스 초기화
def create_tables():
    with app.app_context():
        db.create_all()
        if not Company.query.first():
            companies = [
                {"name": "두산", "code": "000150"},
                {"name": "두산우", "code": "000155"},
                {"name": "두산2우B", "code": "000157"},
                {"name": "두산에너빌리티", "code": "034020"},
                {"name": "두산밥캣", "code": "241560"},
                {"name": "두산퓨얼셀", "code": "336260"},
                {"name": "두산퓨얼셀1우", "code": "33626K"},
                {"name": "두산퓨얼셀2우B", "code": "33626L"},
                {"name": "두산로보틱스", "code": "454910"}
            ]
            for company in companies:
                db.session.add(Company(name=company["name"], code=company["code"]))
            db.session.commit()

create_tables() # 애플리케이션 시작 시 데이터베이스 테이블 생성

# Custom email validator for doosan.com domain
def doosan_email(form, field):
    if not field.data.endswith('@doosan.com'):
        flash('두산 계정만 사용할 수 있습니다.', 'danger')
        raise ValidationError('두산 계정만 사용할 수 있습니다.')

class RegistrationForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email(), doosan_email])
    password = PasswordField('비밀번호', validators=[DataRequired(), EqualTo('confirm', message='비밀번호가 일치하지 않습니다.')])
    confirm = PasswordField('비밀번호 확인')
    submit = SubmitField('가입')

class LoginForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('로그인')

class PostForm(FlaskForm):
    contract_name = StringField('계약명', validators=[DataRequired()])
    company_name = StringField('계약 업체명', validators=[DataRequired()])
    company_code = StringField('계약 업체 코드', validators=[DataRequired()])
    contract_amount = StringField('계약 금액', validators=[DataRequired()])
    contract_period = StringField('계약 기간', validators=[DataRequired()])
    contract_type = StringField('계약 종류', validators=[DataRequired()])
    file = FileField('파일 업로드')
    submit = SubmitField('작성')

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
        email = form.email.data
        if User.query.filter_by(email=email).first():
            flash('아이디가 존재합니다.', 'danger')
        else:
            verification_code = request.form.get('verification_code')
            if verification_code != '123456':
                flash('잘못된 인증번호입니다.', 'danger')
            else:
                new_user = User(email=email, password=form.password.data)
                db.session.add(new_user)
                db.session.commit()
                flash('성공적으로 가입되었습니다!', 'success')
                return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            flash('성공적으로 로그인되었습니다!', 'success')
            return redirect(url_for('index'))
        else:
            flash('이메일 또는 비밀번호가 잘못되었습니다.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    # 로그아웃 로직을 여기에 추가하세요
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('index'))

@app.route('/notices')
def notices():
    return render_template('notices.html')

@app.route('/task2', methods=['GET', 'POST'])
def task2():
    form = PostForm()
    if form.validate_on_submit():
        filename = None
        if form.file.data:
            filename = files.save(form.file.data)
        new_post = Post(title=form.title.data, content=form.content.data, filename=filename)
        db.session.add(new_post)
        db.session.commit()
        flash('게시물이 작성되었습니다.', 'success')
        return redirect(url_for('task2'))
    posts = Post.query.all()
    return render_template('task2.html', form=form, posts=posts)

@app.route('/task2/<int:post_id>')
def task2_detail(post_id):
    post = Post.query.get_or_404(post_id)
    ocr_text = None
    if post.filename:
        file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], post.filename)
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text("text")
            ocr_text = text
        except Exception as e:
            flash(f'OCR 처리 중 오류가 발생했습니다: {str(e)}')
    return render_template('task2_detail.html', post=post, ocr_text=ocr_text)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
