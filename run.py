import extract_msg
import os
import csv

# ✅ Update this path to the folder where your .msg files are extracted
base_folder = r"C:\Users\Admin\Desktop\abacus\Samples_24 Oct"

senders = set()

# Walk through all subfolders
for root, _, files in os.walk(base_folder):
    for file in files:
        if file.lower().endswith(".msg"):
            try:
                msg = extract_msg.Message(os.path.join(root, file))
                sender = msg.sender
                if sender:
                    domain = sender.split("@")[-1] if "@" in sender else "Unknown"
                    senders.add((sender.strip(), domain.strip()))
            except Exception as e:
                print(f"⚠️ Could not read: {file} ({e})")

# Save to CSV
output_file = os.path.join(base_folder, "senders_list.csv")
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Sender", "Domain"])
    writer.writerows(sorted(senders))

print(f"\n✅ Done! Found {len(senders)} unique senders.\n")
for s, d in sorted(senders):
    print(f"{s} — {d}")

print(f"\n📁 List saved to: {output_file}")
