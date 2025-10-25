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

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib

df = pd.read_csv('test1.csv')
df['text_input'] = df['subject'].fillna('') + ' ' + df['reasoning'].fillna('')

counts = df['predicted_category'].value_counts()
rare = counts[counts == 1].index
df['clean_category'] = df['predicted_category'].apply(lambda x: x if x not in rare else 'Other')

X = df['text_input']
y = df['clean_category']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = make_pipeline(
    TfidfVectorizer(),
    SGDClassifier(loss="log_loss", max_iter=1000, tol=1e-3, class_weight='balanced')
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, zero_division=0))

joblib.dump(model, 'email_classifier.pkl')
print("Pipeline model saved as email_classifier.pkl")
vectorizer = model.named_steps['tfidfvectorizer']
joblib.dump(vectorizer, 'vectorizer.pkl')
print("Vectorizer extracted/saved as vectorizer.pkl")
