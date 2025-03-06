from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'  # 設定 SQLite 數據庫
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 定義交易模型
class Transaction(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # 使用 UUID 作為主鍵
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 添加日期時間字段

# 定義類別模型
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' 或 'expense'

# 初始化數據庫
with app.app_context():
    db.create_all()

categories = {
    'income': ['薪水', '獎金', '其他'],
    'expense': ['食物', '交通', '娛樂', '其他']
}

@app.route('/')
def index():
    transactions = Transaction.query.all()  # 從數據庫中獲取所有交易
    income_categories = Category.query.filter_by(type='income').all()
    expense_categories = Category.query.filter_by(type='expense').all()
    
    categories = {
        'income': [{'id': cat.id, 'name': cat.name} for cat in income_categories],
        'expense': [{'id': cat.id, 'name': cat.name} for cat in expense_categories]
    }
    
    return render_template('index.html', transactions=transactions, categories=categories)

@app.route('/add', methods=['POST'])
def add_transaction():
    description = request.form.get('description')
    amount = request.form.get('amount')
    category = request.form.get('category')
    subcategory = request.form.get('subcategory')
    timestamp = request.form.get('timestamp')  # 獲取日期時間

    # 將類別轉換為中文
    if category == 'income':
        category = '收入'
    elif category == 'expense':
        category = '支出'

    transaction_id = str(uuid.uuid4())
    
    new_transaction = Transaction(
        id=transaction_id,
        description=description,
        amount=amount,
        category=category,
        subcategory=subcategory,
        timestamp=datetime.fromisoformat(timestamp)  # 將字符串轉換為 datetime 對象
    )
    
    db.session.add(new_transaction)  # 將新交易添加到數據庫
    db.session.commit()  # 提交更改
    return redirect(url_for('index'))

@app.route('/manage_categories', methods=['GET', 'POST'])
def manage_categories():
    if request.method == 'POST':
        category_type = request.form.get('category_type')
        new_category = request.form.get('new_category')
        if new_category:
            new_category_entry = Category(name=new_category, type=category_type)
            db.session.add(new_category_entry)
            db.session.commit()
        return redirect(url_for('manage_categories'))

    income_categories = Category.query.filter_by(type='income').all()
    expense_categories = Category.query.filter_by(type='expense').all()

    # 將類別轉換為字典格式
    categories = {
        'income': [{'id': cat.id, 'name': cat.name} for cat in income_categories],
        'expense': [{'id': cat.id, 'name': cat.name} for cat in expense_categories]
    }
    return render_template('manage_categories.html', categories=categories)

@app.route('/delete_category', methods=['POST'])
def delete_category():
    category_id = request.form.get('category_id')  # 獲取要刪除的類別 ID
    new_category_name = request.form.get('new_category')  # 獲取轉換到的類別名稱
    category = Category.query.get(category_id)
    
    if category:
        # 轉換已分類的記錄
        for transaction in Transaction.query.filter_by(category=category.name).all():
            transaction.category = new_category_name  # 將類別轉換為新類別
        db.session.delete(category)  # 刪除類別
        db.session.commit()
    return redirect(url_for('manage_categories'))

@app.route('/delete_transactions', methods=['POST'])
def delete_transactions():
    transaction_ids = request.form.getlist('transaction_ids[]')
    Transaction.query.filter(Transaction.id.in_(transaction_ids)).delete(synchronize_session=False)  # 刪除選中的交易
    db.session.commit()  # 提交更改
    return redirect(url_for('index'))

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
    transaction_id = request.form.get('id')
    description = request.form.get('description')
    amount = request.form.get('amount')
    category = request.form.get('category')
    subcategory = request.form.get('subcategory')

    # 將類別轉換為中文
    if category == 'income':
        category = '收入'
    elif category == 'expense':
        category = '支出'

    transaction = Transaction.query.get(transaction_id)
    if transaction:
        transaction.description = description
        transaction.amount = amount
        transaction.category = category
        transaction.subcategory = subcategory
        db.session.commit()  # 提交更改

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
