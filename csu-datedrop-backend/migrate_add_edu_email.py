"""
一次性迁移脚本：为 users 表添加 edu_email 和 edu_email_verified_at 列。
运行方式：  python migrate_add_edu_email.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "datedrop.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 检查列是否已存在
    cur.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cur.fetchall()}

    if "edu_email" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN edu_email TEXT")
        print("✓ 已添加 edu_email 列")
    else:
        print("- edu_email 列已存在，跳过")

    if "edu_email_verified_at" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN edu_email_verified_at DATETIME")
        print("✓ 已添加 edu_email_verified_at 列")
    else:
        print("- edu_email_verified_at 列已存在，跳过")

    conn.commit()
    conn.close()
    print("迁移完成。")


if __name__ == "__main__":
    migrate()
