# School Management System MVP

A secure, fully responsive School Management System deployed on Vercel with a cloud MySQL database hosted on Aiven.

## 🚀 Live Demo
You can access the live application here: 
**[https://school-management-mvp-three.vercel.app](https://school-management-mvp-three.vercel.app)**

## 🔒 Implemented Security Features
This project demonstrates core information security concepts:
*   **Identification & Authentication:** Unique users and secure login.
*   **Hashing, Salt & Pepper:** Passwords are hashed using Bcrypt, secured with a unique salt and a global pepper.
*   **Two-Factor Authentication (2FA):** Integrated with Google Authenticator.
*   **Authorization (RBAC):** Admins and Teachers have different permissions.
*   **Soft Delete:** Users are moved to a Recycle Bin instead of being permanently deleted.
*   **Non-Repudiation:** Audit logs track every action with user IDs and IP addresses.
*   **Backup & Restore:** Database redundancy features.

## 🛠️ Technology Stack
*   **Backend:** Python (Flask)
*   **Database:** MySQL (Aiven Cloud)
*   **Frontend:** HTML, Bootstrap 5, FontAwesome
*   **Deployment:** Vercel
