# ===============================================================
# Project: AI Email Classification & Outlook Automation System
# Developer: SHIVANGI ANILBHAI KAKADIYA 
# Contact: WWSHIVANGI@GMAIL.COM
# Created: October 2025
# Copyright © 2025 SHIVANGI ANILBHAI KAKADIYA. All Rights Reserved.
# 
# License: Proprietary - Internal Evaluation Only
# This software is the intellectual property of SHIVANGI KAKADIYA.
# Redistribution, modification, or commercial use without
# explicit written permission is strictly prohibited.
# ===============================================================

import os
import csv
import tempfile
import zipfile
import joblib
import extract_msg
import email
from email import policy
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CATEGORIES_FILE = 'categories.txt'
CATEGORIES_CSV = 'categories.csv'

model = joblib.load('email_classifier.pkl')

def read_categories():
    if not os.path.exists(CATEGORIES_FILE):
        return []
    with open(CATEGORIES_FILE) as f:
        return sorted([line.strip() for line in f if line.strip()])

def write_categories(categories):
    sorted_cats = sorted(categories)
    with open(CATEGORIES_FILE, 'w') as f:
        for cat in sorted_cats:
            f.write(cat + '\n')
    with open(CATEGORIES_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Category'])
        for cat in sorted_cats:
            writer.writerow([cat])

def get_preview(text):
    lines = [line for line in text.strip().split('\n') if line.strip()]
    preview = lines[0] if lines else ''
    if len(lines) > 1:
        preview += ' ' + lines[1]
    return preview[:100] + "..." if len(preview) > 100 else preview

def parse_eml(file_stream):
    msg = email.message_from_bytes(file_stream.read(), policy=policy.default)
    subject = msg.get('subject', '')
    sender = msg.get('from', '')
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return subject, sender, part.get_content()
                except Exception:
                    continue
        return subject, sender, ""
    else:
        return subject, sender, msg.get_content()

def parse_msg(file_stream):
    msg_obj = extract_msg.Message(file_stream)
    subject = msg_obj.subject or ""
    sender = msg_obj.sender or ""
    body = msg_obj.body or ""
    return subject, sender, body

@app.route('/')
def index():
    categories = read_categories()
    return render_template('index.html', categories=categories)

@app.route('/add_category', methods=['POST'])
def add_category():
    new_category = request.form.get('new_category', '').strip()
    categories = read_categories()
    if not new_category:
        flash('Category name cannot be empty.', 'danger')
    elif new_category in categories:
        flash('Category already exists.', 'danger')
    else:
        categories.append(new_category)
        write_categories(categories)
        flash('Category added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/edit_category', methods=['POST'])
def edit_category():
    old_category = request.form.get('old_category', '').strip()
    edited_category = request.form.get('edited_category', '').strip()
    categories = read_categories()
    if not old_category or not edited_category:
        flash('Both old and new category names must be provided.', 'danger')
    elif old_category not in categories:
        flash('Old category does not exist.', 'danger')
    elif edited_category in categories:
        flash('New category already exists.', 'danger')
    else:
        idx = categories.index(old_category)
        categories[idx] = edited_category
        write_categories(categories)
        flash('Category updated successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete_category', methods=['POST'])
def delete_category():
    category = request.form.get('category', '').strip()
    categories = read_categories()
    if not category:
        flash('No category selected for deletion.', 'danger')
    elif category not in categories:
        flash('Category not found.', 'danger')
    else:
        categories.remove(category)
        write_categories(categories)
        flash('Category deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/classify', methods=['POST'])
def classify():
    file = request.files.get('email_file')
    text = request.form.get('email_text', '').strip()
    if file and (file.filename.endswith('.msg') or file.filename.endswith('.eml')):
        if file.filename.endswith('.msg'):
            subject, sender, body = parse_msg(file)
        else:
            subject, sender, body = parse_eml(file)
    elif text:
        subject, sender, body = text, "", text
    else:
        flash('No email text or file provided.', 'danger')
        return redirect(url_for('index'))
    preview = get_preview(body if body else subject)
    text_input = (subject or '') + " " + (body or '')
    pred = model.predict([text_input])[0]
    proba = model.predict_proba([text_input])[0]
    idx = list(model.classes_).index(pred)
    confidence = f"{proba[idx]*100:.1f}%"
    df = pd.DataFrame([{'Subject': subject, 'Preview': preview, 'Prediction': pred, 'Confidence': confidence}])
    html_table = df.to_html(classes="table table-striped table-hover", index=False)
    return render_template('result.html', table=html_table)

@app.route('/classify_bulk', methods=['POST'])
def classify_bulk():
    file = request.files.get('bulk_email')
    if not file:
        flash("No bulk file provided.", "danger")
        return redirect(url_for('index'))
    filename = file.filename.lower()
    emails = []
    def process(subject, sender, body):
        preview = get_preview(body if body else subject)
        text_input = (subject or '') + " " + (body or '')
        pred = model.predict([text_input])[0]
        proba = model.predict_proba([text_input])[0]
        idx = list(model.classes_).index(pred)
        confidence = f"{proba[idx]*100:.1f}%"
        return {'Subject': subject, 'Preview': preview, 'Prediction': pred, 'Confidence': confidence}
    try:
        if filename.endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, 'upload.zip')
                file.save(zip_path)
                with zipfile.ZipFile(zip_path, 'r') as z:
                    for name in z.namelist():
                        if name.endswith('.msg') or name.endswith('.eml'):
                            with z.open(name) as f:
                                try:
                                    if name.endswith('.msg'):
                                        subject, sender, body = parse_msg(f)
                                    else:
                                        subject, sender, body = parse_eml(f)
                                    emails.append(process(subject, sender, body))
                                except Exception:
                                    continue
        elif filename.endswith('.msg'):
            subject, sender, body = parse_msg(file)
            emails.append(process(subject, sender, body))
        elif filename.endswith('.eml'):
            subject, sender, body = parse_eml(file)
            emails.append(process(subject, sender, body))
        else:
            flash("Only .zip, .msg and .eml are supported.", "danger")
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error processing bulk file: {str(e)}", "danger")
        return redirect(url_for('index'))
    if not emails:
        flash("No valid emails found in file!", "warning")
        return redirect(url_for('index'))
    df = pd.DataFrame(emails)
    html_table = df.to_html(classes="table table-striped table-hover", index=False)
    return render_template('result.html', table=html_table)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
