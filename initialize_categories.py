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

# Load test1.csv and extract unique values from the right column
df = pd.read_csv('test1.csv')
unique_labels = sorted(set(df['predicted_category']))

# Save to categories.txt (one per line)
with open('categories.txt', 'w') as f:
    for label in unique_labels:
        f.write(f"{label}\n")
print("Initialized categories.txt with unique labels from test1.csv.")
