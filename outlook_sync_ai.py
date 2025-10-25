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
import time
import requests
import msal
import joblib
import pandas as pd
from scipy.sparse import vstack

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
CLIENT_ID = "a5be98f5-bae0-44c8-a78c-8ff5fb8561e2"
CLIENT_SECRET = "VSa8Q~BNPuwg-Ueq68Jm4xOhCyfVabVgJ7hBDbRi"
TENANT_ID = "201185f1-1658-4242-bdb3-8b79c8f32b7d"
USER_EMAIL = "alert@jypragroup.com.au"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

MODEL_PATH = "email_classifier.pkl"
PROCESSED_PATH = "sync_history.csv"
FETCH_LIMIT = 10
SLEEP_TIME = 300  # seconds

# ------------------------------------------------------------
# AUTHENTICATION
# ------------------------------------------------------------
def get_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Token retrieval failed: {result}")

# ------------------------------------------------------------
# OUTLOOK FOLDER OPERATIONS
# ------------------------------------------------------------
def get_folders(token):
    """Return list of all Outlook folders."""
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/mailFolders"
    folders = []
    while endpoint:
        resp = requests.get(endpoint, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        folders.extend(data.get("value", []))
        endpoint = data.get("@odata.nextLink")
    print(f"Fetched {len(folders)} folders.")
    return folders


def get_messages(token, folder_id):
    """Return list of all messages in a folder."""
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/mailFolders/{folder_id}/messages?$top={FETCH_LIMIT}"
    emails = []
    while endpoint:
        resp = requests.get(endpoint, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        emails.extend(data.get("value", []))
        endpoint = data.get("@odata.nextLink")
        print(f"Fetched {len(emails)} emails so far...")
        time.sleep(1)
    print(f"Total emails fetched from {folder_id}: {len(emails)}")
    return emails


def get_or_create_folder(token, folder_name, all_folders):
    """Find or create category folder under Inbox."""
    for f in all_folders:
        if f["displayName"].lower() == folder_name.lower():
            return f["id"]

    print(f"Creating folder '{folder_name}' under Inbox...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    create_url = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/mailFolders/inbox/childFolders"
    resp = requests.post(create_url, headers=headers, json={"displayName": folder_name})
    if resp.status_code in [200, 201]:
        folder_id = resp.json()["id"]
        all_folders.append({"displayName": folder_name, "id": folder_id})
        print(f"Created folder: {folder_name}")
        return folder_id
    else:
        print(f"ALERT: Could not create folder '{folder_name}': {resp.status_code} {resp.text}")
        return None


def move_email(token, msg_id, dest_id):
    """Move email to target folder."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/messages/{msg_id}/move"
    payload = {"destinationId": dest_id}
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code in [200, 201]:
        print("Email moved successfully.")
    else:
        print(f"ALERT: Failed to move message {msg_id}: {resp.status_code} - {resp.text}")

# ------------------------------------------------------------
# FILE OPERATIONS
# ------------------------------------------------------------
def load_processed_ids():
    if os.path.exists(PROCESSED_PATH):
        df = pd.read_csv(PROCESSED_PATH)
        return set(df["id"])
    return set()

def save_processed_ids(ids):
    pd.DataFrame({"id": list(ids)}).to_csv(PROCESSED_PATH, index=False)

def load_model():
    return joblib.load(MODEL_PATH)

def clean_texts(texts):
    return [t if isinstance(t, str) and t.strip() else "" for t in texts]

# ------------------------------------------------------------
# RETRAIN MODEL (ATTEMPT WITH ALERTS)
# ------------------------------------------------------------
def retrain_model(model, texts, categories):
    texts = clean_texts(texts)
    if not texts or not categories:
        print("No valid data for retraining.")
        return

    vectorizer = model.named_steps["tfidfvectorizer"]
    clf = model.named_steps["sgdclassifier"]
    X = vectorizer.transform(texts)
    categories = pd.Series(categories).astype(str)

    known_classes = getattr(clf, "classes_", [])
    all_classes = sorted(set(known_classes) | set(categories.unique()) | {"__dummy__"})

    try:
        if len(categories.unique()) == 1:
            dummy_label = "__dummy__"
            print(f"Single-label batch detected for '{categories.unique()[0]}' — safe retrain using dummy label.")
            X_aug = vstack([X, X[0]])
            augmented_y = list(categories) + [dummy_label]
            clf.partial_fit(X_aug, augmented_y, classes=all_classes)
        else:
            clf.partial_fit(X, categories, classes=all_classes)

        joblib.dump(model, MODEL_PATH)
        print(f"Retrained successfully on {len(categories)} samples (total {len(all_classes)} categories).")

    except Exception as e:
        print(f"ALERT: Retrain consistency issue — model retained safely. Error: {e}")
        # Continue loop; do not exit script

# ------------------------------------------------------------
# CLASSIFICATION FUNCTION
# ------------------------------------------------------------
def classify_emails(model, emails):
    results = []
    for mail in emails:
        text = f"{(mail.get('subject') or '')} {(mail.get('bodyPreview') or '')}".strip()
        pred = model.predict([text])[0]
        try:
            proba = model.predict_proba([text])[0]
            conf = proba[list(model.classes_).index(pred)]
        except Exception:
            conf = 0.0
        results.append({
            "id": mail["id"],
            "subject": mail.get("subject", ""),
            "category": pred,
            "confidence": conf,
            "folder": mail.get("parentFolderId", "")
        })
    return results

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    print("Starting Outlook AI auto-classifier and organiser.")
    model = load_model()
    processed_ids = load_processed_ids()

    while True:
        try:
            token = get_token()
        except Exception as e:
            print(f"ALERT: Authentication failed: {e}")
            time.sleep(60)
            continue

        folders = get_folders(token)
        skip_folders = ["deleted items", "junk email", "drafts", "archive"]
        all_results, new_ids = [], set()

        for folder in folders:
            name = folder.get("displayName", "").lower()
            if any(skip in name for skip in skip_folders):
                print(f"Skipping folder: {folder.get('displayName')}")
                continue

            print(f"\nProcessing folder: {folder.get('displayName')}")
            emails = get_messages(token, folder["id"])
            new_emails = [m for m in emails if m["id"] not in processed_ids]
            if not new_emails:
                continue

            results = classify_emails(model, new_emails)
            all_results.extend(results)
            new_ids.update([r["id"] for r in results])

            for r in results:
                cat = r["category"]
                msg_id = r["id"]
                folder_id = get_or_create_folder(token, cat, folders)
                if folder_id:
                    move_email(token, msg_id, folder_id)

        if all_results:
            print(f"Total new emails processed: {len(all_results)}")
            texts = [r["subject"] for r in all_results]
            labels = [r["category"] for r in all_results]
            retrain_model(model, texts, labels)
            processed_ids |= new_ids
            save_processed_ids(processed_ids)
        else:
            print("No new emails available for classification.")

        print("\nSleeping 5 minutes before next check...\n")
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()
