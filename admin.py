from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Admin password from environment
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def get_db_connection():
    conn = sqlite3.connect('data/leads.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Вы успешно вошли в систему!', 'success')
        else:
            flash('Неверный пароль!', 'error')
    
    if request.args.get('logout'):
        session.pop('admin_logged_in', None)
        flash('Вы вышли из системы!', 'info')
        return redirect(url_for('admin'))
    
    if 'admin_logged_in' not in session:
        return render_template('admin/login.html')
    
    # Показываем дашборд если авторизованы
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads ORDER BY created_at DESC').fetchall()
    conn.close()
    
    # Statistics
    total_leads = len(leads)
    today_leads = len([lead for lead in leads if 
                      datetime.strptime(lead['created_at'], '%Y-%m-%d %H:%M:%S').date() == datetime.now().date()])
    
    return render_template('admin/dashboard.html', 
                         leads=leads, 
                         total_leads=total_leads,
                         today_leads=today_leads)

@app.route('/admin/lead/<int:lead_id>')
def lead_details(lead_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    lead = conn.execute('SELECT * FROM leads WHERE id = ?', (lead_id,)).fetchone()
    conn.close()
    
    if lead is None:
        flash('Заявка не найдена!', 'error')
        return redirect(url_for('admin'))
    
    return render_template('admin/lead_details.html', lead=lead)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
