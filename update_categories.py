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

df = pd.read_csv('test1.csv')
categories = sorted(df['predicted_category'].dropna().unique())
with open('categories.txt', 'w') as f:
    for c in categories:
        f.write(f"{c}\n")
print("Category list updated in categories.txt.")
